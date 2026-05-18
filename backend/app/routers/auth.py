from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.admin_auth import require_admin_token
from app.utils.json_store import load_json, save_json
from app.services.external_settings import (
    ExternalSettingsUpdate,
    external_settings_status,
    update_external_settings,
)

router = APIRouter(tags=["auth"])

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
AUTH_PATH = DATA_DIR / "auth_users.json"
DEFAULT_SITES = ["설비팀", "건축기술팀"]


def _decode_header(value: str | None) -> str:
    return unquote(value or "").strip()


def _unique_sites(sites: list[str], *, include_defaults: bool = False) -> list[str]:
    result: list[str] = []
    base = [*DEFAULT_SITES, *sites] if include_defaults else sites
    for site in base:
        clean = str(site or "").strip()
        if clean and clean not in result:
            result.append(clean)
    return result


def _normalize(data: dict, *, include_defaults: bool = False) -> dict:
    users = []
    for user in data.get("users", []):
        name = str(user.get("name", "")).strip()
        sabun = str(user.get("sabun", "")).strip()
        if not name or not sabun:
            continue
        users.append({
            "name": name,
            "sabun": sabun,
            "can_manage_all": bool(user.get("can_manage_all", False)),
        })
    return {"users": users, "sites": _unique_sites(data.get("sites", []), include_defaults=include_defaults)}


def _load() -> dict:
    raw = load_json(AUTH_PATH, default={"users": [], "sites": []})
    return _normalize(raw, include_defaults=not AUTH_PATH.exists())


def _save(data: dict) -> None:
    save_json(AUTH_PATH, _normalize(data))


def _find_user(users: list[dict], name: str, sabun: str) -> dict | None:
    clean_name = _decode_header(name)
    clean_sabun = _decode_header(sabun)
    return next((u for u in users if u.get("name") == clean_name and u.get("sabun") == clean_sabun), None)


def get_auth_sites() -> list[str]:
    return _load().get("sites", [])


def auth_site_exists(site_name: str) -> bool:
    return site_name in get_auth_sites()


def is_known_user(name: str | None, sabun: str | None) -> bool:
    return _find_user(_load().get("users", []), name or "", sabun or "") is not None


def is_manager_user(name: str | None, sabun: str | None) -> bool:
    user = _find_user(_load().get("users", []), name or "", sabun or "")
    return bool(user and user.get("can_manage_all"))


@router.get("/auth/sites")
def get_sites():
    data = _load()
    return {"sites": data.get("sites", [])}


class LoginRequest(BaseModel):
    name: str
    sabun: str
    site_name: str = ""


@router.post("/auth/login")
def login(body: LoginRequest):
    name = body.name.strip()
    sabun = body.sabun.strip()
    if not name or not sabun:
        raise HTTPException(status_code=400, detail="이름과 사번을 입력해주세요.")

    data = _load()
    matched = next(
        (u for u in data.get("users", []) if u["name"] == name and u["sabun"] == sabun),
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
            "can_manage_all": bool(matched.get("can_manage_all", False)),
        },
    }


class SiteNamePayload(BaseModel):
    name: str = Field(..., min_length=1)


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1)
    sabun: str = Field(..., min_length=1)
    can_manage_all: bool = False


class UserUpdate(BaseModel):
    name: str | None = None
    sabun: str | None = None
    can_manage_all: bool | None = None


@router.get("/admin/verify", dependencies=[Depends(require_admin_token)])
def verify_admin():
    return {"ok": True}


@router.get("/admin/auth-data", dependencies=[Depends(require_admin_token)])
def get_auth_data():
    data = _load()
    return {"ok": True, "users": data.get("users", []), "sites": data.get("sites", [])}


@router.get("/admin/external-settings", dependencies=[Depends(require_admin_token)])
def get_admin_external_settings():
    return external_settings_status()


@router.put("/admin/external-settings", dependencies=[Depends(require_admin_token)])
def put_admin_external_settings(body: ExternalSettingsUpdate):
    return update_external_settings(body)


@router.post("/admin/auth-sites", status_code=201, dependencies=[Depends(require_admin_token)])
def create_auth_site(body: SiteNamePayload):
    data = _load()
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="현장명을 입력하세요.")
    if name in data.get("sites", []):
        raise HTTPException(status_code=409, detail="이미 등록된 현장명입니다.")
    data.setdefault("sites", []).append(name)
    _save(data)
    return {"ok": True, "sites": _load().get("sites", [])}


@router.put("/admin/auth-sites/{site_name}", dependencies=[Depends(require_admin_token)])
def update_auth_site(site_name: str, body: SiteNamePayload):
    data = _load()
    original = unquote(site_name).strip()
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="현장명을 입력하세요.")
    sites = data.get("sites", [])
    if original not in sites:
        raise HTTPException(status_code=404, detail="현장명을 찾을 수 없습니다.")
    if name != original and name in sites:
        raise HTTPException(status_code=409, detail="이미 등록된 현장명입니다.")
    data["sites"] = [name if site == original else site for site in sites]
    _save(data)
    return {"ok": True, "sites": _load().get("sites", [])}


@router.delete("/admin/auth-sites/{site_name}", dependencies=[Depends(require_admin_token)])
def delete_auth_site(site_name: str):
    data = _load()
    target = unquote(site_name).strip()
    before = len(data.get("sites", []))
    data["sites"] = [site for site in data.get("sites", []) if site != target]
    if len(data["sites"]) == before:
        raise HTTPException(status_code=404, detail="현장명을 찾을 수 없습니다.")
    _save(data)
    return {"ok": True, "sites": _load().get("sites", [])}


@router.post("/admin/auth-users", status_code=201, dependencies=[Depends(require_admin_token)])
def create_auth_user(body: UserCreate):
    data = _load()
    name = body.name.strip()
    sabun = body.sabun.strip()
    if any(user.get("sabun") == sabun for user in data.get("users", [])):
        raise HTTPException(status_code=409, detail="이미 등록된 사번입니다.")
    user = {"name": name, "sabun": sabun, "can_manage_all": body.can_manage_all}
    data.setdefault("users", []).append(user)
    _save(data)
    return {"ok": True, "user": user}


@router.put("/admin/auth-users/{sabun}", dependencies=[Depends(require_admin_token)])
def update_auth_user(sabun: str, body: UserUpdate):
    data = _load()
    target = unquote(sabun).strip()
    users = data.get("users", [])
    idx = next((i for i, user in enumerate(users) if user.get("sabun") == target), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    next_sabun = body.sabun.strip() if body.sabun is not None else users[idx]["sabun"]
    if next_sabun != target and any(user.get("sabun") == next_sabun for user in users):
        raise HTTPException(status_code=409, detail="이미 등록된 사번입니다.")
    if body.name is not None:
        users[idx]["name"] = body.name.strip()
    users[idx]["sabun"] = next_sabun
    if body.can_manage_all is not None:
        users[idx]["can_manage_all"] = body.can_manage_all
    _save(data)
    return {"ok": True, "user": _load().get("users", [])[idx]}


@router.delete("/admin/auth-users/{sabun}", dependencies=[Depends(require_admin_token)])
def delete_auth_user(sabun: str):
    data = _load()
    target = unquote(sabun).strip()
    before = len(data.get("users", []))
    data["users"] = [user for user in data.get("users", []) if user.get("sabun") != target]
    if len(data["users"]) == before:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    _save(data)
    return {"ok": True}
