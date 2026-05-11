from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter

from app.services.standard_repository import StandardRepository

router = APIRouter(prefix="/mobile", tags=["mobile-field"])
repo = StandardRepository()


@router.get("/status")
def mobile_status():
    """Field-mode readiness summary for the mobile PWA."""
    items = repo.list_items()
    categories = repo.categories()
    return {
        "ok": True,
        "phase": "18.1-gemini-ai-provider",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "field_mode": {
            "offline_local_json": True,
            "recent_items": True,
            "favorites": True,
            "checklist_local_storage": True,
            "field_notes_local_storage": True,
            "install_prompt": True,
            "service_worker_update_notice": True,
        },
        "standard_count": len(items),
        "categories": categories,
    }
