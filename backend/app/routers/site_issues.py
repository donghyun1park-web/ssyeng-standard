from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["site-issues"])

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
SITES_PATH = DATA_DIR / "sites.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load() -> dict:
    if not SITES_PATH.exists():
        return {"sites": [], "drawing_reviews": [], "site_issues": []}
    try:
        return json.loads(SITES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"sites": [], "drawing_reviews": [], "site_issues": []}


def _save(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SITES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Models ──────────────────────────────────────────────────────────────────

class SiteCreate(BaseModel):
    site_name: str = Field(..., min_length=1)
    site_scale: str = ""
    construction_start: str = ""
    construction_end: str = ""
    manager_name: str = ""
    description: str = ""


class SiteUpdate(BaseModel):
    site_name: str | None = None
    site_scale: str | None = None
    construction_start: str | None = None
    construction_end: str | None = None
    manager_name: str | None = None
    description: str | None = None


class DrawingReviewCreate(BaseModel):
    site_id: str
    category: str = ""
    location: str = ""
    review_content: str = Field(..., min_length=1)
    action_plan: str = ""
    status: Literal["검토중", "협의중", "반영완료", "보류"] = "검토중"


class DrawingReviewUpdate(BaseModel):
    category: str | None = None
    location: str | None = None
    review_content: str | None = None
    action_plan: str | None = None
    status: Literal["검토중", "협의중", "반영완료", "보류"] | None = None


class SiteIssueCreate(BaseModel):
    site_id: str
    trade: str = ""
    location: str = ""
    issue_content: str = Field(..., min_length=1)
    cause: str = ""
    action_content: str = ""
    status: Literal["조치필요", "검토중", "협의중", "조치완료"] = "조치필요"
    related_standard: str = ""
    related_page: str = ""


class SiteIssueUpdate(BaseModel):
    trade: str | None = None
    location: str | None = None
    issue_content: str | None = None
    cause: str | None = None
    action_content: str | None = None
    status: Literal["조치필요", "검토중", "협의중", "조치완료"] | None = None
    related_standard: str | None = None
    related_page: str | None = None


# ── Sites ────────────────────────────────────────────────────────────────────

@router.get("/sites")
def list_sites():
    data = _load()
    sites = data.get("sites", [])
    reviews = data.get("drawing_reviews", [])
    issues = data.get("site_issues", [])
    result = []
    for site in sites:
        sid = site["id"]
        result.append({
            **site,
            "drawing_review_count": sum(1 for r in reviews if r.get("site_id") == sid),
            "issue_count": sum(1 for i in issues if i.get("site_id") == sid),
        })
    return {"sites": result, "count": len(result)}


@router.get("/sites/{site_id}")
def get_site(site_id: str):
    data = _load()
    site = next((s for s in data.get("sites", []) if s["id"] == site_id), None)
    if not site:
        raise HTTPException(status_code=404, detail="현장을 찾을 수 없습니다.")
    reviews = [r for r in data.get("drawing_reviews", []) if r.get("site_id") == site_id]
    issues = [i for i in data.get("site_issues", []) if i.get("site_id") == site_id]
    return {"site": site, "drawing_reviews": reviews, "site_issues": issues}


@router.post("/sites", status_code=201)
def create_site(body: SiteCreate):
    data = _load()
    site = {
        "id": f"site-{uuid.uuid4().hex[:10]}",
        "site_name": body.site_name,
        "site_scale": body.site_scale,
        "construction_start": body.construction_start,
        "construction_end": body.construction_end,
        "manager_name": body.manager_name,
        "description": body.description,
        "created_at": _now(),
        "updated_at": _now(),
    }
    data.setdefault("sites", []).append(site)
    _save(data)
    return {"ok": True, "site": site}


@router.put("/sites/{site_id}")
def update_site(site_id: str, body: SiteUpdate):
    data = _load()
    idx = next((i for i, s in enumerate(data.get("sites", [])) if s["id"] == site_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="현장을 찾을 수 없습니다.")
    site = data["sites"][idx]
    for field in ("site_name", "site_scale", "construction_start", "construction_end", "manager_name", "description"):
        val = getattr(body, field)
        if val is not None:
            site[field] = val
    site["updated_at"] = _now()
    _save(data)
    return {"ok": True, "site": site}


@router.delete("/sites/{site_id}")
def delete_site(site_id: str):
    data = _load()
    before = len(data.get("sites", []))
    data["sites"] = [s for s in data.get("sites", []) if s["id"] != site_id]
    data["drawing_reviews"] = [r for r in data.get("drawing_reviews", []) if r.get("site_id") != site_id]
    data["site_issues"] = [i for i in data.get("site_issues", []) if i.get("site_id") != site_id]
    if len(data["sites"]) == before:
        raise HTTPException(status_code=404, detail="현장을 찾을 수 없습니다.")
    _save(data)
    return {"ok": True}


# ── Drawing Reviews ──────────────────────────────────────────────────────────

@router.post("/drawing-reviews", status_code=201)
def create_drawing_review(body: DrawingReviewCreate):
    data = _load()
    if not any(s["id"] == body.site_id for s in data.get("sites", [])):
        raise HTTPException(status_code=404, detail="현장을 찾을 수 없습니다.")
    review = {
        "id": f"dr-{uuid.uuid4().hex[:10]}",
        "site_id": body.site_id,
        "category": body.category,
        "location": body.location,
        "review_content": body.review_content,
        "action_plan": body.action_plan,
        "status": body.status,
        "created_at": _now(),
        "updated_at": _now(),
    }
    data.setdefault("drawing_reviews", []).append(review)
    _save(data)
    return {"ok": True, "review": review}


@router.put("/drawing-reviews/{review_id}")
def update_drawing_review(review_id: str, body: DrawingReviewUpdate):
    data = _load()
    idx = next((i for i, r in enumerate(data.get("drawing_reviews", [])) if r["id"] == review_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="도면검토를 찾을 수 없습니다.")
    review = data["drawing_reviews"][idx]
    for field in ("category", "location", "review_content", "action_plan", "status"):
        val = getattr(body, field)
        if val is not None:
            review[field] = val
    review["updated_at"] = _now()
    _save(data)
    return {"ok": True, "review": review}


@router.delete("/drawing-reviews/{review_id}")
def delete_drawing_review(review_id: str):
    data = _load()
    before = len(data.get("drawing_reviews", []))
    data["drawing_reviews"] = [r for r in data.get("drawing_reviews", []) if r["id"] != review_id]
    if len(data["drawing_reviews"]) == before:
        raise HTTPException(status_code=404, detail="도면검토를 찾을 수 없습니다.")
    _save(data)
    return {"ok": True}


# ── Site Issues ───────────────────────────────────────────────────────────────

@router.post("/site-issues", status_code=201)
def create_site_issue(body: SiteIssueCreate):
    data = _load()
    if not any(s["id"] == body.site_id for s in data.get("sites", [])):
        raise HTTPException(status_code=404, detail="현장을 찾을 수 없습니다.")
    issue = {
        "id": f"iss-{uuid.uuid4().hex[:10]}",
        "site_id": body.site_id,
        "trade": body.trade,
        "location": body.location,
        "issue_content": body.issue_content,
        "cause": body.cause,
        "action_content": body.action_content,
        "status": body.status,
        "related_standard": body.related_standard,
        "related_page": body.related_page,
        "created_at": _now(),
        "updated_at": _now(),
    }
    data.setdefault("site_issues", []).append(issue)
    _save(data)
    return {"ok": True, "issue": issue}


@router.put("/site-issues/{issue_id}")
def update_site_issue(issue_id: str, body: SiteIssueUpdate):
    data = _load()
    idx = next((i for i, iss in enumerate(data.get("site_issues", [])) if iss["id"] == issue_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="이슈를 찾을 수 없습니다.")
    issue = data["site_issues"][idx]
    for field in ("trade", "location", "issue_content", "cause", "action_content", "status", "related_standard", "related_page"):
        val = getattr(body, field)
        if val is not None:
            issue[field] = val
    issue["updated_at"] = _now()
    _save(data)
    return {"ok": True, "issue": issue}


@router.delete("/site-issues/{issue_id}")
def delete_site_issue(issue_id: str):
    data = _load()
    before = len(data.get("site_issues", []))
    data["site_issues"] = [i for i in data.get("site_issues", []) if i["id"] != issue_id]
    if len(data["site_issues"]) == before:
        raise HTTPException(status_code=404, detail="이슈를 찾을 수 없습니다.")
    _save(data)
    return {"ok": True}
