"""
사전 탑재 스크립트: 회사 시공표준 PDF를 pdfplumber 고급파싱으로 rag_index에 등록.
실행: python scripts/preload_document.py
"""
import json
import re
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ─── 경로 설정 ──────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
BACKEND_DIR  = PROJECT_ROOT / "backend"
DATA_DIR     = BACKEND_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
INDEX_PATH   = DATA_DIR / "rag_index.json"

# Docker 빌드 시: /app/backend/data/preload/ 경로
# 로컬 실행 시: C:\Users\User\Downloads\ 경로 (fallback)
_PRELOAD_DIR = PROJECT_ROOT / "backend" / "data" / "preload"
_LOCAL_PATH  = Path(r"C:\Users\User\Downloads\23년 공동주택 설계 및 시공 표준화 개정_20231124.pdf")
PDF_SOURCE = (
    next(_PRELOAD_DIR.glob("*.pdf"), None)
    or (_LOCAL_PATH if _LOCAL_PATH.exists() else None)
)

DOCUMENT_TITLE   = "공동주택 설계 및 시공 표준화 개정 지침"
DOCUMENT_VERSION = "2023 개정판"
REVISION_DATE    = "2023-11-24"

# ─── 헬퍼 ───────────────────────────────────────────────────────────────────
_TOKEN_RE       = re.compile(r"[0-9A-Za-z가-힣_+#./-]+")
_PAGE_MARKER_RE = re.compile(r"\[p\.(\d+)\]")
_CHAPTER_RE     = re.compile(r"^제\s*(\d+)\s*장\s+(.+)$", re.MULTILINE)
_SECTION_RE     = re.compile(r"^(\d+\.\d+(?:\.\d+)*)\s+(.+)$", re.MULTILINE)


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if len(t.strip()) >= 2]


def _extract_chapter_section(text: str):
    chapter = section = clause = ""
    ch = _CHAPTER_RE.search(text)
    if ch:
        chapter = f"제{ch.group(1)}장 {ch.group(2).strip()}"
    secs = list(_SECTION_RE.finditer(text))
    if secs:
        best = secs[-1]
        num  = best.group(1)
        title = best.group(2).strip()
        parts = num.split(".")
        if len(parts) >= 3:
            clause  = f"{num} {title}"
            section = ".".join(parts[:2]) + " …"
        elif len(parts) == 2:
            section = f"{num} {title}"
        else:
            chapter = chapter or f"{num} {title}"
    return chapter, section, clause


def _chunk_text_with_pages(text: str, chunk_size=900, overlap=120):
    clean = re.sub(r"\s+", " ", text or "").strip()
    if not clean:
        return []

    page_positions = []
    for m in _PAGE_MARKER_RE.finditer(clean):
        page_positions.append((m.start(), int(m.group(1))))

    def page_at(pos):
        p = 1
        for cp, pg in page_positions:
            if cp <= pos:
                p = pg
            else:
                break
        return p

    chunks = []
    start = 0
    while start < len(clean):
        end = min(start + chunk_size, len(clean))
        chunk_text = clean[start:end].strip()
        if chunk_text:
            ch, sec, cla = _extract_chapter_section(chunk_text)
            chunks.append({
                "text":       chunk_text,
                "page_start": page_at(start),
                "page_end":   page_at(end - 1),
                "chapter":    ch,
                "section":    sec,
                "clause":     cla,
            })
        if end >= len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def parse_pdf_advanced(pdf_path: Path) -> str:
    """pdfplumber 고급 파싱 — 표+텍스트 통합, 한국어 최적화."""
    try:
        import pdfplumber
    except ImportError:
        print("pdfplumber 없음 → pip install pdfplumber 후 재실행")
        sys.exit(1)

    pages = []
    print(f"  PDF 파싱 중: {pdf_path.name}")
    with pdfplumber.open(str(pdf_path)) as pdf:
        total = len(pdf.pages)
        for page_no, page in enumerate(pdf.pages, start=1):
            if page_no % 10 == 0:
                print(f"    {page_no}/{total} 페이지 처리 중...")
            text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
            tables = page.extract_tables() or []
            table_text = ""
            for table in tables:
                for row in table:
                    if row:
                        cleaned = [cell.strip() if cell else "" for cell in row]
                        line = " | ".join(c for c in cleaned if c)
                        if line:
                            table_text += line + "\n"
            combined = (text + ("\n" + table_text if table_text else "")).strip()
            if combined:
                pages.append(f"[p.{page_no}]\n{combined}")
    if not pages:
        print("  경고: 텍스트 추출 실패. 스캔 이미지 PDF일 수 있습니다.")
        sys.exit(1)
    full_text = "\n\n".join(pages)
    print(f"  → {len(pages)}페이지, {len(full_text):,}자 추출 완료")
    return full_text


def load_index() -> dict:
    if INDEX_PATH.exists():
        try:
            return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"version": 2, "updated_at": None, "documents": [], "chunks": []}


def save_index(data: dict):
    data["updated_at"] = _now_iso()
    INDEX_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  rag_index.json 저장 완료: 문서 {len(data['documents'])}개, 청크 {len(data['chunks'])}개")


def main():
    print("=" * 60)
    print("사전 탑재: 회사 시공표준 PDF 고급파싱 업로드")
    print("=" * 60)

    if PDF_SOURCE is None or not PDF_SOURCE.exists():
        print(f"오류: PDF 파일을 찾을 수 없습니다.\n  preload 폴더: {_PRELOAD_DIR}\n  로컬 경로: {_LOCAL_PATH}")
        sys.exit(1)
    print(f"  PDF 소스: {PDF_SOURCE}")

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. 기존 같은 제목 문서 정리 ─────────────────────────────────────────
    data = load_index()
    OLD_TITLES = [
        DOCUMENT_TITLE,
        "23년 공동주택 설계 및 시공 표준화 개정_20231124",
        "23년 공동주택 설계 및 시공 표준화 개정_20231124",
    ]
    old_ids = {d["id"] for d in data.get("documents", []) if d.get("title") in OLD_TITLES or d.get("id").startswith("doc-4325cb03d1ad")}
    if old_ids:
        print(f"  기존 문서 {len(old_ids)}개 제거 중...")
        data["documents"] = [d for d in data.get("documents", []) if d["id"] not in old_ids]
        data["chunks"]    = [c for c in data.get("chunks", [])    if c.get("document_id") not in old_ids]
        for old_id in old_ids:
            for f in DOCUMENTS_DIR.glob(f"{old_id}_*"):
                f.unlink(missing_ok=True)
                print(f"    삭제: {f.name}")

    # ── 2. PDF 고급파싱 ─────────────────────────────────────────────────────
    print("\n[1단계] pdfplumber 고급파싱...")
    full_text = parse_pdf_advanced(PDF_SOURCE)

    # ── 3. 청크 생성 ────────────────────────────────────────────────────────
    print("\n[2단계] 청크 분할 중...")
    raw_chunks = _chunk_text_with_pages(full_text, chunk_size=900, overlap=120)
    print(f"  → {len(raw_chunks)}개 청크 생성")

    # ── 4. 문서 등록 ────────────────────────────────────────────────────────
    doc_id    = f"doc-{uuid.uuid4().hex[:12]}"
    safe_name = re.sub(r"[^0-9A-Za-z가-힣_.-]+", "_", PDF_SOURCE.name).strip("_")
    stored_filename = f"{doc_id}_{safe_name}"
    stored_path     = DOCUMENTS_DIR / stored_filename

    print(f"\n[3단계] 파일 복사: {stored_filename}")
    shutil.copyfile(PDF_SOURCE, stored_path)

    pdf_url = f"/api/rag/documents/{doc_id}/file"

    document = {
        "id":               doc_id,
        "title":            DOCUMENT_TITLE,
        "filename":         PDF_SOURCE.name,
        "stored_filename":  stored_filename,
        "extension":        ".pdf",
        "version":          DOCUMENT_VERSION,
        "revision_date":    REVISION_DATE,
        "pdf_url":          pdf_url,
        "uploaded_at":      _now_iso(),
        "chunk_count":      len(raw_chunks),
        "character_count":  len(full_text),
        "is_active":        True,
        "parse_method":     "pdfplumber-advanced",
        "source_type":      "company_standard",
    }
    data.setdefault("documents", []).append(document)
    print(f"  문서 등록: {DOCUMENT_TITLE} (ID: {doc_id})")

    # ── 5. 청크 저장 ────────────────────────────────────────────────────────
    print("\n[4단계] 청크 인덱싱...")
    for idx, chunk_data in enumerate(raw_chunks, start=1):
        data.setdefault("chunks", []).append({
            "id":             f"{doc_id}-c{idx:04d}",
            "document_id":    doc_id,
            "document_title": DOCUMENT_TITLE,
            "filename":       PDF_SOURCE.name,
            "chunk_index":    idx,
            "chapter":        chunk_data.get("chapter", ""),
            "section":        chunk_data.get("section", ""),
            "clause":         chunk_data.get("clause", ""),
            "page_start":     chunk_data.get("page_start", 1),
            "page_end":       chunk_data.get("page_end", 1),
            "text":           chunk_data["text"],
            "tokens":         _tokenize(chunk_data["text"]),
            "pdf_url":        pdf_url,
            "version":        DOCUMENT_VERSION,
            "source_type":    "company_standard",
        })

    # ── 6. 저장 ─────────────────────────────────────────────────────────────
    print("\n[5단계] rag_index.json 저장...")
    save_index(data)

    # ── 결과 요약 ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("✅ 완료!")
    print(f"  문서명: {DOCUMENT_TITLE}")
    print(f"  버전: {DOCUMENT_VERSION}")
    print(f"  청크 수: {len(raw_chunks)}")
    print(f"  문자 수: {len(full_text):,}")
    print(f"  파일: {stored_filename}")
    print("=" * 60)


if __name__ == "__main__":
    main()
