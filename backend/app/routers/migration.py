from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from app.services.admin_auth import require_admin_token
from app.services.data_migration import DataMigrationService

router = APIRouter(prefix="/migration", tags=["migration"])
service = DataMigrationService()


def _download_response(filename: str, content: bytes, media_type: str) -> Response:
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type=media_type, headers=headers)


@router.get("/status")
def status():
    return service.status()


@router.get("/template")
def download_template(format: str = Query(default="csv", pattern="^(csv|json)$")):
    filename, content, media_type = service.template(format)
    return _download_response(filename, content, media_type)


@router.post("/validate", dependencies=[Depends(require_admin_token)])
async def validate_upload(file: UploadFile = File(...)):
    try:
        content = await file.read()
        return service.validate_upload(content, file.filename or "upload")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/import", dependencies=[Depends(require_admin_token)])
async def stage_import(file: UploadFile = File(...), note: str = Form(default="")):
    try:
        content = await file.read()
        return service.stage_upload(content, file.filename or "upload", note=note)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/batches", dependencies=[Depends(require_admin_token)])
def list_batches():
    return service.list_batches()


@router.get("/batches/{batch_id}", dependencies=[Depends(require_admin_token)])
def get_batch(batch_id: str):
    try:
        batch = service.get_batch(batch_id)
        batch["items_preview"] = batch.get("items", [])[:20]
        return batch
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="batch not found")


@router.post("/batches/{batch_id}/commit", dependencies=[Depends(require_admin_token)])
def commit_batch(batch_id: str, mode: str = Query(default="upsert", pattern="^(append|upsert|replace)$")):
    try:
        return service.commit_batch(batch_id, mode=mode)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="batch not found")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/batches/{batch_id}", dependencies=[Depends(require_admin_token)])
def delete_batch(batch_id: str):
    try:
        return service.delete_batch(batch_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="batch not found")


@router.get("/export", dependencies=[Depends(require_admin_token)])
def export_current(format: str = Query(default="json", pattern="^(csv|json)$")):
    try:
        filename, content, media_type = service.export_current(format)
        return _download_response(filename, content, media_type)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
