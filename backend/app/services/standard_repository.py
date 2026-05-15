import json
import re
from pathlib import Path
from typing import Any, ClassVar

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "standard_items.json"
RAG_INDEX_PATH = Path(__file__).resolve().parents[2] / "data" / "rag_index.json"
DOCUMENT_DIR = Path(__file__).resolve().parents[2] / "data" / "documents"

_GENERIC_TITLE_WORDS = {
    "목적",
    "설계기준",
    "시공기준",
    "표준화",
    "일반사항",
    "참조사항",
    "참고기준",
}

class StandardRepository:
    _shared_cache: ClassVar[dict[tuple[str, str], tuple[tuple[float, float], list[dict[str, Any]]]]] = {}

    def __init__(self, data_path: Path = DATA_PATH, rag_index_path: Path = RAG_INDEX_PATH):
        self.data_path = data_path
        self.rag_index_path = rag_index_path
        self._cache_key = (str(self.data_path.resolve()), str(self.rag_index_path.resolve()))
        self._mtime = (-1.0, -1.0)
        self._items = []

    def reload_if_changed(self, force: bool = False) -> None:
        mtime = (
            self.data_path.stat().st_mtime if self.data_path.exists() else 0.0,
            self.rag_index_path.stat().st_mtime if self.rag_index_path.exists() else 0.0,
        )
        if not force:
            cached = self._shared_cache.get(self._cache_key)
            if cached and cached[0] == mtime:
                self._mtime = mtime
                self._items = cached[1]
                return

        if force or mtime != self._mtime:
            rag_items = self._load_rag_items()
            self._items = rag_items if rag_items else self._load_items()
            self._mtime = mtime
            self._shared_cache[self._cache_key] = (mtime, self._items)

    def _load_items(self) -> list[dict[str, Any]]:
        with self.data_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("standard_items.json must be a list")
        return data

    def _load_rag_items(self) -> list[dict[str, Any]]:
        if not self.rag_index_path.exists():
            return []
        try:
            with self.rag_index_path.open("r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except Exception:
            return []

        documents = data.get("documents", [])
        if isinstance(documents, list):
            pdf_items = []
            for document in documents:
                if isinstance(document, dict) and document.get("extension") == ".pdf":
                    pdf_items.extend(self._load_pdf_page_items(document))
            if pdf_items:
                return pdf_items

        chunks = data.get("chunks", [])
        if not isinstance(chunks, list):
            return []

        rag_items: list[dict[str, Any]] = []
        for chunk in chunks:
            if not isinstance(chunk, dict):
                continue
            text = chunk.get("text") or ""
            doc_title = chunk.get("document_title") or chunk.get("filename") or "업로드 문서"
            chunk_index = chunk.get("chunk_index")
            rag_items.append({
                "id": f"rag-{chunk.get('id')}",
                "category": "업로드 문서",
                "section": doc_title,
                "title": f"{doc_title} · chunk {chunk_index}",
                "summary": text[:220],
                "body": text,
                "keywords": [
                    "RAG",
                    "업로드 문서",
                    "PDF",
                    str(doc_title),
                    str(chunk.get("filename") or ""),
                ],
                "checklist": [],
                "source": "rag",
                "document_id": chunk.get("document_id"),
                "filename": chunk.get("filename"),
                "chunk_index": chunk_index,
            })
        return rag_items

    def _load_pdf_page_items(self, document: dict[str, Any]) -> list[dict[str, Any]]:
        if PdfReader is None:
            return []
        document_id = str(document.get("id") or "")
        stored_filename = str(document.get("stored_filename") or "")
        if not document_id or not stored_filename:
            return []

        file_path = (DOCUMENT_DIR / stored_filename).resolve()
        base_dir = DOCUMENT_DIR.resolve()
        if file_path != base_dir and base_dir not in file_path.parents:
            return []
        if not file_path.exists():
            return []

        doc_title = str(document.get("title") or document.get("filename") or "업로드 PDF")
        filename = str(document.get("filename") or stored_filename)

        try:
            reader = PdfReader(str(file_path))
        except Exception:
            return []

        items: list[dict[str, Any]] = []
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""
            headings = self._extract_pdf_page_headings(page_text)
            page_title = self._choose_pdf_page_title(headings) or f"{doc_title} p.{page_number}"
            title_text = " ".join([page_title, *headings])
            items.append({
                "id": f"rag-{document_id}-p{page_number:04d}",
                "category": "업로드 PDF",
                "section": doc_title,
                "title": page_title,
                "summary": " · ".join(headings[:5]) if headings else f"{doc_title} 원본 PDF {page_number}페이지",
                "body": "",
                "keywords": [
                    "PDF",
                    "업로드 PDF",
                    str(doc_title),
                    str(filename),
                    f"p.{page_number}",
                    f"{page_number}페이지",
                    *headings,
                ],
                "checklist": [],
                "source": "rag",
                "source_mode": "pdf-title-page",
                "document_id": document_id,
                "filename": filename,
                "pdf_page": page_number,
                "pdf_url": f"/api/rag/documents/{document_id}/file#page={page_number}",
                "indexed_text": title_text,
            })
        return items

    @staticmethod
    def _extract_pdf_page_headings(text: str) -> list[str]:
        headings: list[str] = []
        for raw_line in (text or "").splitlines():
            line = re.sub(r"\s+", " ", raw_line).strip(" -·\t")
            if not line:
                continue
            if len(line) < 4 or len(line) > 80:
                continue
            if line.isdigit():
                continue
            if "Ssangyong" in line or "Engineering & Construction" in line:
                continue
            if line == "공동주택 설계 및 시공 표준화":
                continue
            if re.match(r"^\d{1,2}\s+[가-힣A-Za-z].+", line):
                headings.append(line)
            elif re.match(r"^\d{1,2}-\d+\s+.+", line):
                headings.append(line)
            elif re.match(r"^\d+\)\s+.+", line):
                headings.append(line)
            elif re.match(r"^[①-⑳]\s*.+", line):
                headings.append(line)

        deduped: list[str] = []
        for heading in headings:
            if heading not in deduped:
                deduped.append(heading)
        return deduped[:12]

    @staticmethod
    def _choose_pdf_page_title(headings: list[str]) -> str | None:
        if not headings:
            return None
        for heading in headings:
            if re.match(r"^\d+\)\s+.+", heading):
                label = re.sub(r"^\d+\)\s+", "", heading).strip()
                if label not in _GENERIC_TITLE_WORDS and len(label) >= 5:
                    return heading
        for heading in headings:
            if re.match(r"^\d{1,2}-\d+\s+.+", heading):
                return heading
        return headings[0]

    def list_items(self, category: str | None = None, section: str | None = None) -> list[dict[str, Any]]:
        self.reload_if_changed()
        items = self._items
        if category and category != "전체":
            items = [item for item in items if item.get("category") == category]
        if section:
            items = [item for item in items if item.get("section") == section]
        return items

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        self.reload_if_changed()
        return next((item for item in self._items if item.get("id") == item_id), None)

    def search(self, query: str = "", category: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        q = query.strip().lower()
        candidates = self.list_items(category=category)
        if not q:
            return candidates[:limit]

        scored: list[tuple[int, dict[str, Any]]] = []
        for item in candidates:
            fields = [
                item.get("id", ""),
                item.get("category", ""),
                item.get("section", ""),
                item.get("title", ""),
                item.get("summary", ""),
                item.get("body", ""),
                " ".join(item.get("keywords", [])),
            ]
            haystack = " ".join(fields).lower()
            if q in haystack:
                score = 0
                if q in item.get("title", "").lower():
                    score += 5
                if q in item.get("summary", "").lower():
                    score += 3
                if q in " ".join(item.get("keywords", [])).lower():
                    score += 3
                score += haystack.count(q)
                scored.append((score, item))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def categories(self) -> dict[str, list[str]]:
        self.reload_if_changed()
        categories = sorted({item.get("category", "미분류") for item in self._items})
        sections = sorted({item.get("section", "미분류") for item in self._items})
        return {"categories": categories, "sections": sections}
