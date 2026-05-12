from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.admin_auth import require_admin_token
from app.services.document_rag import DocumentRagStore

router = APIRouter(tags=["rag"])
rag_store = DocumentRagStore()


class TextIndexRequest(BaseModel):
    title: str = Field(default="manual_text", min_length=1, max_length=120)
    text: str = Field(..., min_length=10)


@router.get("/rag/status")
def rag_status():
    return rag_store.status()


@router.get("/rag/documents")
def rag_documents():
    documents = rag_store.list_documents()
    return {"ok": True, "count": len(documents), "documents": documents}


@router.get("/rag/documents/{document_id}/file")
def rag_document_file(document_id: str):
    file_info = rag_store.get_document_file(document_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="document file not found")
    file_path, filename = file_info
    return FileResponse(file_path, media_type="application/pdf", filename=filename, content_disposition_type="inline")


@router.get("/rag/search")
def rag_search(q: str, limit: int = 5):
    limit = max(1, min(limit, 20))
    return {"ok": True, "query": q, "results": rag_store.search(q, limit=limit)}


@router.post("/rag/index-text", dependencies=[Depends(require_admin_token)])
def rag_index_text(payload: TextIndexRequest):
    try:
        document = rag_store.add_text_document(payload.text, title=payload.title)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "document": document, "status": rag_store.status()}


@router.post("/rag/upload", dependencies=[Depends(require_admin_token)])
async def rag_upload(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    document_title: str | None = Form(default=None),
    version: str = Form(default=""),
    revision_date: str = Form(default=""),
):
    suffix = Path(file.filename or "").suffix.lower()
    if not suffix:
        raise HTTPException(status_code=400, detail="파일 확장자를 확인할 수 없습니다.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp_path = Path(temp.name)
        temp.write(await file.read())

    try:
        document = rag_store.add_document(
            temp_path,
            original_filename=file.filename,
            title=title,
            document_title=document_title,
            version=version,
            revision_date=revision_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        temp_path.unlink(missing_ok=True)

    return {"ok": True, "document": document, "status": rag_store.status()}


@router.post("/rag/parse-pdf", dependencies=[Depends(require_admin_token)])
async def rag_parse_pdf(
    file: UploadFile = File(...),
    document_title: str = Form(...),
    version: str = Form(default=""),
    revision_date: str = Form(default=""),
):
    """Firecrawl /parse를 사용해 PDF를 파싱하고 RAG 인덱스에 추가합니다."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix != ".pdf":
        raise HTTPException(status_code=400, detail="Firecrawl 파싱은 PDF 파일만 지원합니다.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        temp_path = Path(temp.name)
        temp.write(await file.read())

    try:
        document = await rag_store.add_document_firecrawl(
            temp_path,
            original_filename=file.filename,
            document_title=document_title,
            version=version,
            revision_date=revision_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"고급 PDF 파싱 오류: {exc}") from exc
    finally:
        temp_path.unlink(missing_ok=True)

    return {"ok": True, "document": document, "status": rag_store.status()}
