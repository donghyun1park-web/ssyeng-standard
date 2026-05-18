from __future__ import annotations

import json
import math
import os
import re
import shutil
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from app.utils.json_store import save_json

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

try:
    from docx import Document
except Exception:  # pragma: no cover
    Document = None

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DOCUMENT_DIR = DATA_DIR / "documents"
INDEX_PATH = DATA_DIR / "rag_index.json"
SUPPORTED_EXTENSIONS = {".txt", ".md", ".json", ".pdf", ".docx"}

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_+#./-]+")
_PAGE_MARKER_RE = re.compile(r"\[p\.(\d+)\]")
_CHAPTER_RE = re.compile(r"^제\s*(\d+)\s*장\s+(.+)$", re.MULTILINE)
_SECTION_RE = re.compile(r"^(\d+\.\d+(?:\.\d+)*)\s+(.+)$", re.MULTILINE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text or "") if len(token.strip()) >= 2]


def _extract_chapter_section(text: str) -> tuple[str, str, str]:
    chapter = ""
    section = ""
    clause = ""
    ch_match = _CHAPTER_RE.search(text)
    if ch_match:
        chapter = f"제{ch_match.group(1)}장 {ch_match.group(2).strip()}"
    sec_matches = list(_SECTION_RE.finditer(text))
    if sec_matches:
        best = sec_matches[-1]
        num = best.group(1)
        title = best.group(2).strip()
        parts = num.split(".")
        if len(parts) >= 3:
            clause = f"{num} {title}"
            section = ".".join(parts[:2]) + " …"
        elif len(parts) == 2:
            section = f"{num} {title}"
        else:
            chapter = chapter or f"{num} {title}"
    return chapter, section, clause


def _chunk_text_with_pages(
    text: str, *, chunk_size: int = 900, overlap: int = 120
) -> list[dict]:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if not clean:
        return []

    # Build a page-position map from [p.N] markers
    page_positions: list[tuple[int, int]] = []  # (char_pos, page_no)
    for m in _PAGE_MARKER_RE.finditer(clean):
        page_positions.append((m.start(), int(m.group(1))))

    def page_at(pos: int) -> int:
        page = 1
        for char_pos, pg in page_positions:
            if char_pos <= pos:
                page = pg
            else:
                break
        return page

    chunks: list[dict] = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunk_text = clean[start:end].strip()
        if chunk_text:
            page_start = page_at(start)
            page_end = page_at(end - 1)
            ch, sec, cla = _extract_chapter_section(chunk_text)
            chunks.append({
                "text": chunk_text,
                "page_start": page_start,
                "page_end": page_end,
                "chapter": ch,
                "section": sec,
                "clause": cla,
            })
        if end >= len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def _chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if not clean:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def _read_txt(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "cp949", "euc-kr"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def _read_json(path: Path) -> str:
    try:
        data = json.loads(_read_txt(path))
        return json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        return _read_txt(path)


def _read_pdf(path: Path) -> str:
    if PdfReader is None:
        raise ValueError("PDF 읽기를 위해 pypdf가 필요합니다.")
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page_no, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append(f"[p.{page_no}]\n{text}")
    return "\n\n".join(pages)


def _read_docx(path: Path) -> str:
    if Document is None:
        raise ValueError("DOCX 읽기를 위해 python-docx가 필요합니다.")
    doc = Document(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md"}:
        return _read_txt(path)
    if suffix == ".json":
        return _read_json(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".docx":
        return _read_docx(path)
    raise ValueError(f"지원하지 않는 파일 형식입니다: {suffix}")


def _read_pdf_advanced(path: Path) -> str:
    """pdfplumber를 사용한 고급 PDF 텍스트 추출.
    pypdf보다 컬럼 레이아웃·표·한국어 텍스트 추출 품질이 높습니다.
    """
    try:
        import pdfplumber
    except ImportError:
        raise ValueError(
            "pdfplumber가 설치되지 않았습니다. "
            "`pip install pdfplumber` 후 백엔드를 재시작하세요."
        )

    pages: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page_no, page in enumerate(pdf.pages, start=1):
            # extract_text: 공백 허용 범위를 넓혀 붙어 있는 글자 분리
            text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
            # 표(table)도 별도 추출해서 이어 붙임
            tables = page.extract_tables() or []
            table_text = ""
            for table in tables:
                for row in table:
                    if row:
                        cleaned = [cell.strip() if cell else "" for cell in row]
                        table_text += " | ".join(cleaned) + "\n"
            combined = (text + ("\n" + table_text if table_text else "")).strip()
            if combined:
                pages.append(f"[p.{page_no}]\n{combined}")

    if not pages:
        raise ValueError("PDF에서 텍스트를 추출하지 못했습니다. 스캔 이미지 PDF는 지원되지 않습니다.")
    return "\n\n".join(pages)


class DocumentRagStore:
    def __init__(self, index_path: Path = INDEX_PATH, document_dir: Path = DOCUMENT_DIR):
        self.index_path = index_path
        self.document_dir = document_dir
        self.document_dir.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        if not self.index_path.exists():
            return {"version": 2, "updated_at": None, "documents": [], "chunks": []}
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            return {"version": 2, "updated_at": None, "documents": [], "chunks": []}

    def _save(self, data: dict) -> None:
        data["updated_at"] = _now_iso()
        save_json(self.index_path, data)

    def status(self) -> dict:
        data = self._load()
        return {
            "ok": True,
            "documents": len(data.get("documents", [])),
            "chunks": len(data.get("chunks", [])),
            "updated_at": data.get("updated_at"),
            "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        }

    def list_documents(self) -> list[dict]:
        return self._load().get("documents", [])

    def get_document_file(self, document_id: str) -> tuple[Path, str] | None:
        document = next((doc for doc in self.list_documents() if doc.get("id") == document_id), None)
        if not document:
            return None
        stored_filename = str(document.get("stored_filename") or "")
        if not stored_filename:
            return None
        base_dir = self.document_dir.resolve()
        file_path = (self.document_dir / stored_filename).resolve()
        if file_path != base_dir and base_dir not in file_path.parents:
            return None
        if not file_path.exists() or not file_path.is_file():
            return None
        return file_path, str(document.get("filename") or file_path.name)

    def add_document(
        self,
        source_path: Path,
        *,
        original_filename: str | None = None,
        title: str | None = None,
        document_title: str | None = None,
        version: str = "",
        revision_date: str = "",
        parsed_text: str | None = None,
    ) -> dict:
        suffix = source_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"지원하지 않는 파일 형식입니다. 지원 형식: {', '.join(sorted(SUPPORTED_EXTENSIONS))}")

        doc_id = f"doc-{uuid.uuid4().hex[:12]}"
        safe_name = re.sub(r"[^0-9A-Za-z가-힣_.-]+", "_", original_filename or source_path.name).strip("_") or f"document{suffix}"
        stored_path = self.document_dir / f"{doc_id}_{safe_name}"
        shutil.copyfile(source_path, stored_path)

        text = parsed_text if parsed_text else extract_text(stored_path)
        raw_chunks = _chunk_text_with_pages(text)
        if not raw_chunks:
            raise ValueError("문서에서 검색 가능한 텍스트를 추출하지 못했습니다.")

        doc_title = document_title or title or Path(original_filename or source_path.name).stem
        pdf_url = f"/api/rag/documents/{doc_id}/file"

        data = self._load()
        document = {
            "id": doc_id,
            "title": doc_title,
            "filename": original_filename or source_path.name,
            "stored_filename": stored_path.name,
            "extension": suffix,
            "version": version,
            "revision_date": revision_date,
            "pdf_url": pdf_url,
            "uploaded_at": _now_iso(),
            "chunk_count": len(raw_chunks),
            "character_count": len(text),
            "is_active": True,
        }
        data.setdefault("documents", []).append(document)

        for idx, chunk_data in enumerate(raw_chunks, start=1):
            chunk_id = f"{doc_id}-c{idx:04d}"
            data.setdefault("chunks", []).append({
                "id": chunk_id,
                "document_id": doc_id,
                "document_title": doc_title,
                "filename": document["filename"],
                "chunk_index": idx,
                "chapter": chunk_data.get("chapter", ""),
                "section": chunk_data.get("section", ""),
                "clause": chunk_data.get("clause", ""),
                "page_start": chunk_data.get("page_start", 1),
                "page_end": chunk_data.get("page_end", 1),
                "text": chunk_data["text"],
                "tokens": _tokenize(chunk_data["text"]),
                "pdf_url": pdf_url,
                "version": version,
                "revision_date": revision_date,
            })
        self._save(data)
        return document

    async def add_document_firecrawl(
        self,
        source_path: Path,
        *,
        original_filename: str | None = None,
        document_title: str | None = None,
        version: str = "",
        revision_date: str = "",
    ) -> dict:
        """pdfplumber를 사용한 고급 PDF 파싱 (구 Firecrawl 엔드포인트와 동일한 시그니처 유지)."""
        parsed_text = _read_pdf_advanced(source_path)
        return self.add_document(
            source_path,
            original_filename=original_filename,
            document_title=document_title,
            version=version,
            revision_date=revision_date,
            parsed_text=parsed_text,
        )

    def add_text_document(self, text: str, *, title: str = "manual_text") -> dict:
        temp = self.document_dir / f"tmp_{uuid.uuid4().hex}.txt"
        temp.write_text(text, encoding="utf-8")
        try:
            return self.add_document(temp, original_filename=f"{title}.txt", title=title)
        finally:
            temp.unlink(missing_ok=True)

    def search(self, query: str, *, limit: int = 5) -> list[dict]:
        """검색어 매칭 정밀도 우선 — TF-IDF + 매칭률 + 구문 인접성 가산."""
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        data = self._load()
        chunks = data.get("chunks", [])
        if not chunks:
            return []

        q_counter = Counter(q_tokens)
        q_unique = list(q_counter.keys())
        n_q_unique = len(q_unique)

        doc_freq: Counter[str] = Counter()
        for chunk in chunks:
            doc_freq.update(set(chunk.get("tokens", [])))
        n_docs = max(1, len(chunks))

        # 검색 구문 — phrase / bigram 매칭용
        query_phrase = re.sub(r"\s+", " ", query.strip().lower())
        bigrams = [
            f"{q_tokens[i]} {q_tokens[i + 1]}".lower()
            for i in range(len(q_tokens) - 1)
        ]

        # (matched_count, score, payload) — 1순위: 매칭 토큰 수, 2순위: TF-IDF 점수
        scored: list[tuple[int, float, dict]] = []
        for chunk in chunks:
            tokens = chunk.get("tokens", [])
            if not tokens:
                continue
            counter = Counter(tokens)
            text_lower = chunk.get("text", "").lower()

            # 1. 검색어 토큰 중 청크에 등장한 수
            matched = sum(1 for t in q_unique if counter.get(t, 0) or t in text_lower)
            if matched == 0:
                continue

            # 2. 다중 검색어일 때, 매칭 토큰이 1개뿐이면 제외 (관련성 낮음)
            if n_q_unique >= 3 and matched < 2:
                continue

            # 3. 기본 TF-IDF 점수 (정렬 보조)
            score = 0.0
            for token, q_weight in q_counter.items():
                tf = counter.get(token, 0)
                if not tf:
                    continue
                idf = math.log((n_docs + 1) / (doc_freq[token] + 1)) + 1.0
                score += (1.0 + math.log(tf)) * idf * q_weight

            # 4. 구문 인접성 보너스
            if n_q_unique >= 2 and query_phrase and query_phrase in text_lower:
                score *= 4.0  # 전체 구문 정확히 등장
            elif bigrams:
                bigram_hits = sum(1 for bg in bigrams if bg in text_lower)
                if bigram_hits > 0:
                    score *= 1.0 + 0.6 * bigram_hits  # 인접 2-그램 1개당 ×1.6

            if score > 0:
                payload = {k: v for k, v in chunk.items() if k != "tokens"}
                payload["score"] = round(score, 4)
                payload["matched_terms"] = matched
                scored.append((matched, score, payload))

        # 정렬: 매칭 토큰 수(많은 순) → TF-IDF 점수(높은 순)
        scored.sort(key=lambda x: (-x[0], -x[1]))
        return [payload for _, _, payload in scored[:limit]]

    def build_context(self, chunks: Iterable[dict]) -> str:
        blocks = []
        for idx, chunk in enumerate(chunks, start=1):
            page_info = f"p.{chunk.get('page_start')}" if chunk.get('page_start') else ""
            chapter_info = " > ".join(filter(None, [chunk.get('chapter'), chunk.get('section'), chunk.get('clause')]))
            blocks.append(
                f"[문서 근거 {idx}]\n"
                f"문서: {chunk.get('document_title')}\n"
                f"위치: {chapter_info or '미상'} {page_info}\n"
                f"파일: {chunk.get('filename')}\n"
                f"내용: {chunk.get('text')}"
            )
        return "\n\n".join(blocks)
