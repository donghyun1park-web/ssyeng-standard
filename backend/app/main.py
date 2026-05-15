import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import ask, auth, checklists, diagnostics, external, mcp, mobile, notices, rag, site_issues, standards, search_quality, migration


DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "https://VERCEL_FRONTEND_URL_TO_BE_SET",
]


def cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOW_ORIGINS") or os.getenv("FRONTEND_URL") or os.getenv("VERCEL_FRONTEND_URL") or ""
    extra = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
    origins: list[str] = []
    for origin in [*DEFAULT_CORS_ORIGINS, *extra]:
        if origin and origin not in origins:
            origins.append(origin)
    return origins

app = FastAPI(
    title="Facility Standard API",
    description="설비 시공표준 PWA Phase 18.1 Gemini AI Provider 백엔드 API",
    version="0.18.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"ok": True, "service": "facility-standard-app-backend", "phase": "v2.0-facility-standard"}

app.include_router(standards.router, prefix="/api")
app.include_router(rag.router, prefix="/api")
app.include_router(mcp.router, prefix="/api")
app.include_router(external.router, prefix="/api")
app.include_router(ask.router, prefix="/api")
app.include_router(diagnostics.router, prefix="/api")
app.include_router(mobile.router, prefix="/api")
app.include_router(search_quality.router, prefix="/api")
app.include_router(migration.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(notices.router, prefix="/api")
app.include_router(site_issues.router, prefix="/api")
app.include_router(checklists.router, prefix="/api")

from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DIST_DIR = PROJECT_ROOT / "dist"
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")
    if (DIST_DIR / "brand").exists():
        app.mount("/brand", StaticFiles(directory=DIST_DIR / "brand"), name="brand")
    if (DIST_DIR / "icons").exists():
        app.mount("/icons", StaticFiles(directory=DIST_DIR / "icons"), name="icons")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        api_or_docs = full_path.startswith(("api/", "docs", "openapi.json", "redoc"))
        if api_or_docs:
            return {"detail": "Not Found"}
        return FileResponse(DIST_DIR / "index.html")
