from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["auth"])

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
AUTH_PATH = DATA_DIR / "auth_users.json"


def _load() -> dict:
    if not AUTH_PATH.exists():
        return {"users": [], "sites": []}
    try:
        return json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"users": [], "sites": []}


@router.get("/auth/sites")
def get_sites():
    """현장 목록 반환 (로그인 화면 현장 선택용)."""
    data = _load()
    return {"sites": data.get("sites", [])}


class LoginRequest(BaseModel):
    name: str
    sabun: str
    site_name: str = ""


@router.post("/auth/login")
def login(body: LoginRequest):
    """이름 + 사번 인증. 일치하는 사용자가 있으면 OK 반환."""
    name = body.name.strip()
    sabun = body.sabun.strip()
    if not name or not sabun:
        raise HTTPException(status_code=400, detail="이름과 사번을 입력해주세요.")

    data = _load()
    users = data.get("users", [])
    matched = next(
        (u for u in users if u["name"] == name and u["sabun"] == sabun),
        None,
    )
    if not matched:
        raise HTTPException(status_code=401, detail="이름 또는 사번이 올바르지 않습니다.")

    return {
        "ok": True,
        "user": {
            "name": matched["name"],
            "sabun": matched["sabun"],
            "site_name": body.site_name,
        },
    }
