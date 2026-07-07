from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.routers.auth import is_manager_user
from app.services.admin_auth import has_valid_admin_token
from app.utils.json_store import load_json, save_json

router = APIRouter(tags=["notices"])

DATA_DIR      = Path(__file__).resolve().parents[2] / "data"
NOTICES_PATH  = DATA_DIR / "notices.json"
FILES_DIR     = DATA_DIR / "notice_files"
ALLOWED_EXT   = {".pdf", ".jpg", ".jpeg", ".png", ".docx", ".xlsx", ".txt", ".hwp"}
MAX_FILE_MB   = 20


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    return load_json(NOTICES_PATH, default={"notices": []})


def _save(data: dict) -> None:
    save_json(NOTICES_PATH, data)


def _decode_header(value: str | None) -> str:
    return unquote(value or "").strip()


def _check_notice_manager(token: str | None, user_name: str | None, user_sabun: str | None) -> None:
    if has_valid_admin_token(token):
        return
    if is_manager_user(_decode_header(user_name), _decode_header(user_sabun)):
        return
    raise HTTPException(status_code=403, detail="공지사항 관리 권한이 필요합니다.")


# ── 공지 목록 ────────────────────────────────────────────────────────────────

@router.get("/notices")
def list_notices():
    data = _load()
    notices = sorted(data.get("notices", []), key=lambda n: n.get("created_at", ""), reverse=True)
    return {"notices": notices, "total": len(notices)}


# ── 공지 상세 ────────────────────────────────────────────────────────────────

@router.get("/notices/{notice_id}")
def get_notice(notice_id: str):
    data = _load()
    notice = next((n for n in data.get("notices", []) if n["id"] == notice_id), None)
    if not notice:
        raise HTTPException(status_code=404, detail="공지를 찾을 수 없습니다.")
    return notice


# ── 공지 등록 (관리자) ───────────────────────────────────────────────────────

@router.post("/notices")
async def create_notice(
    title:   str        = Form(...),
    content: str        = Form(...),
    poster:  str        = Form(...),
    file:    UploadFile = File(None),
    x_admin_token: str  = Header(default="", alias="X-Admin-Token"),
    x_user_name: str = Header(default="", alias="X-User-Name"),
    x_user_sabun: str = Header(default="", alias="X-User-Sabun"),
):
    _check_notice_manager(x_admin_token, x_user_name, x_user_sabun)

    if not title.strip():
        raise HTTPException(status_code=400, detail="제목을 입력해주세요.")
    if not content.strip():
        raise HTTPException(status_code=400, detail="내용을 입력해주세요.")

    notice_id = f"notice-{uuid.uuid4().hex[:10]}"
    file_info = None

    if file and file.filename:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_EXT:
            raise HTTPException(status_code=400, detail=f"허용되지 않는 파일 형식입니다. 허용: {', '.join(sorted(ALLOWED_EXT))}")
        content_bytes = await file.read()
        if len(content_bytes) > MAX_FILE_MB * 1024 * 1024:
            raise HTTPException(status_code=400, detail=f"파일 크기가 {MAX_FILE_MB}MB를 초과합니다.")
        FILES_DIR.mkdir(parents=True, exist_ok=True)
        stored_name = f"{notice_id}{suffix}"
        (FILES_DIR / stored_name).write_bytes(content_bytes)
        file_info = {
            "original_name": file.filename,
            "stored_name":   stored_name,
            "size_bytes":    len(content_bytes),
            "file_url":      f"/api/notices/{notice_id}/file",
        }

    notice = {
        "id":         notice_id,
        "title":      title.strip(),
        "content":    content.strip(),
        "poster":     poster.strip(),
        "date":       datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "file":       file_info,
        "created_at": _now(),
    }

    data = _load()
    data.setdefault("notices", []).insert(0, notice)
    _save(data)
    return {"ok": True, "notice": notice}


# ── 공지 삭제 (관리자) ───────────────────────────────────────────────────────

@router.delete("/notices/{notice_id}")
def delete_notice(
    notice_id: str,
    x_admin_token: str = Header(default="", alias="X-Admin-Token"),
    x_user_name: str = Header(default="", alias="X-User-Name"),
    x_user_sabun: str = Header(default="", alias="X-User-Sabun"),
):
    _check_notice_manager(x_admin_token, x_user_name, x_user_sabun)
    data = _load()
    notices = data.get("notices", [])
    target = next((n for n in notices if n["id"] == notice_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="공지를 찾을 수 없습니다.")

    # 첨부파일 삭제
    if target.get("file") and target["file"].get("stored_name"):
        fp = FILES_DIR / target["file"]["stored_name"]
        if fp.exists():
            fp.unlink()

    data["notices"] = [n for n in notices if n["id"] != notice_id]
    _save(data)
    return {"ok": True}


# ── 첨부파일 다운로드 ────────────────────────────────────────────────────────

@router.get("/notices/{notice_id}/file")
def download_notice_file(notice_id: str):
    data = _load()
    notice = next((n for n in data.get("notices", []) if n["id"] == notice_id), None)
    if not notice or not notice.get("file"):
        raise HTTPException(status_code=404, detail="첨부파일이 없습니다.")
    stored_name = notice["file"]["stored_name"]
    fp = FILES_DIR / stored_name
    if not fp.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(
        path=fp,
        filename=notice["file"]["original_name"],
        media_type="application/octet-stream",
    )
