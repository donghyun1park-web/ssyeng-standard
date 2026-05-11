from fastapi import APIRouter, HTTPException, Query
from app.services.standard_repository import StandardRepository

router = APIRouter(tags=["standards"])
repo = StandardRepository()

@router.get("/standards")
def list_standards(category: str | None = None, section: str | None = None):
    items = repo.list_items(category=category, section=section)
    return {"count": len(items), "items": items}

@router.get("/standards/{item_id}")
def get_standard(item_id: str):
    item = repo.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="standard item not found")
    return item

@router.get("/search")
def search_standards(
    q: str = Query(default="", description="검색어"),
    category: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
):
    items = repo.search(query=q, category=category, limit=limit)
    return {"query": q, "category": category or "전체", "count": len(items), "items": items}

@router.get("/categories")
def list_categories():
    return repo.categories()
