from fastapi import APIRouter
from app.services.diagnostics import DiagnosticsService

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])
service = DiagnosticsService()


@router.get("/status")
def status():
    return service.status()


@router.get("/checks")
def checks():
    return service.run_checks()
