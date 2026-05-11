from __future__ import annotations

from fastapi import APIRouter, Query, Path
from pydantic import BaseModel, Field

from app.services.external_standards import ExternalStandardsAdapter

router = APIRouter(tags=["external-standards"])
adapter = ExternalStandardsAdapter()


class UnifiedSearchRequest(BaseModel):
    query: str = Field(default="", max_length=300)
    sources: list[str] = Field(default_factory=lambda: ["law", "kcsc"])
    limit: int = Field(default=5, ge=1, le=20)


@router.get("/external/status")
def external_status():
    return adapter.status()


@router.get("/external/law/search")
def search_law(q: str = Query(default=""), limit: int = Query(default=5, ge=1, le=20)):
    return adapter.search_law(q, limit=limit)


@router.get("/external/kcsc/search")
def search_kcsc(
    q: str = Query(default=""),
    limit: int = Query(default=5, ge=1, le=20),
    types: list[str] | None = Query(default=None),
    final_only: bool = Query(default=True),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
):
    return adapter.search_kcsc(
        q,
        limit=limit,
        types=types,
        final_only=final_only,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/external/search")
def unified_search(payload: UnifiedSearchRequest):
    clean_sources = [source for source in payload.sources if source in {"law", "kcsc"}]
    return adapter.unified_search(payload.query, sources=clean_sources or ["law", "kcsc"], limit=payload.limit)



@router.get("/external/kcsc/viewer/{standard_type}/{code}")
def get_kcsc_viewer(
    standard_type: str = Path(..., description="KCS, KDS, EXCS, SMCS"),
    code: str = Path(..., description="KCSC CodeViewer code"),
):
    return adapter.get_kcsc_viewer(standard_type, code)
