import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import audit, business, demo, employee, health, scheduling, training
from app.api.v1.router import v1_router
from app.api.v1.console.routes import router as console_router
from app.middleware.audit import AuditMiddleware
from app.core.db import get_db
from app.services.roles_seed import seed_permissions_and_roles

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    """Seed default permissions/roles on startup."""
    db = next(get_db())
    try:
        try:
            seed_permissions_and_roles(db)
        except Exception as exc:
            logger.exception("Startup seeding failed; continuing without seeds: %s", exc)
        yield
    finally:
        db.close()

app = FastAPI(title="Cloud Workforce System", version="0.2.0", lifespan=lifespan)

if os.getenv("ENABLE_AUDIT", "0") == "1":
    app.add_middleware(AuditMiddleware)

_templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=_templates_dir)

# Legacy MVP routes
app.include_router(health.router)
app.include_router(business.router)
app.include_router(employee.router)
app.include_router(scheduling.router)
app.include_router(training.router)
app.include_router(audit.router)
app.include_router(demo.router)

# V1 plane routes
app.include_router(v1_router)
app.include_router(console_router)

# Compute frontend paths relative to this repository for portability
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_DEV_INDEX = PROJECT_ROOT / "frontend" / "index.html"

# Mount frontend static files at /static (prefer assets/ if present)
# Prefer serving the built frontend if present; otherwise expose the dev frontend directory
if FRONTEND_DIST.exists() and FRONTEND_DIST.is_dir():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists() and assets_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(assets_dir)), name="frontend-static")
    else:
        app.mount("/static", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend-static")
else:
    # Expose the frontend directory so the dev index.html and /src assets can be served directly
    dev_frontend_dir = PROJECT_ROOT / "frontend"
    if dev_frontend_dir.exists() and dev_frontend_dir.is_dir():
        app.mount("/static", StaticFiles(directory=str(dev_frontend_dir), html=True), name="frontend-static")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui(request: Request):
    """Return the built frontend index.html if available; otherwise return the dev index.html
    (useful for local development) and finally fall back to server-side template.
    """
    # 1) Built production dist
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

    # 2) Vite dev build index (unbuilt /src-based entry)
    if FRONTEND_DEV_INDEX.exists():
        return HTMLResponse(content=FRONTEND_DEV_INDEX.read_text(encoding="utf-8"))

    # 3) Fallback to server-side template rendering
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/{full_path:path}", response_class=HTMLResponse, include_in_schema=False)
def spa_fallback(request: Request, full_path: str):
    """Fallback route for SPA client-side routing. Serves files from the built frontend when present
    otherwise tries to serve files from the dev frontend directory, and finally returns index.html
    so the client router can handle the path.
    """
    # 1) If the requested path exists as a file in the dist directory, serve it directly.
    candidate = FRONTEND_DIST / full_path
    if candidate.exists() and candidate.is_file():
        return FileResponse(str(candidate))

    # 2) If the requested path exists in the dev frontend dir, serve it
    dev_candidate = PROJECT_ROOT / "frontend" / full_path
    if dev_candidate.exists() and dev_candidate.is_file():
        return FileResponse(str(dev_candidate))

    # 3) If built index.html exists, serve it (SPA entry)
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))

    # 4) If dev index.html exists, serve that
    if FRONTEND_DEV_INDEX.exists():
        return HTMLResponse(content=FRONTEND_DEV_INDEX.read_text(encoding="utf-8"))

    # 5) Final fallback to template rendering when built UI not present
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/roles/", response_class=HTMLResponse, include_in_schema=False)
def roles_ui(request: Request):
    return templates.TemplateResponse("roles.html", {"request": request})
