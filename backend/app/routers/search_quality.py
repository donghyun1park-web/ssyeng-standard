from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.search_quality import SearchQualityService

router = APIRouter(prefix="/search-quality", tags=["search-quality"])
service = SearchQualityService()


class AdvancedSearchRequest(BaseModel):
    query: str = Field(default="", max_length=300)
    category: str | None = None
    section: str | None = None
    limit: int = Field(default=20, ge=1, le=100)


@router.get("/status")
def status():
    return service.status()


@router.get("/suggestions")
def suggestions(q: str = Query(default=""), limit: int = Query(default=8, ge=1, le=20)):
    return {"ok": True, "query": q, "suggestions": service.suggestions(q, limit=limit)}


@router.get("/terms")
def terms(limit: int = Query(default=20, ge=1, le=100)):
    return {"ok": True, "terms": service.term_frequency(limit=limit)}


@router.post("/search")
def search(payload: AdvancedSearchRequest):
    return service.search(
        payload.query,
        category=payload.category,
        section=payload.section,
        limit=payload.limit,
    )
