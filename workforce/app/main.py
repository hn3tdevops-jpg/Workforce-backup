import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
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

app.mount("/assets", StaticFiles(directory="/home/hn3t/workforce/frontend/dist/assets"), name="frontend-assets")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui(request: Request):
    frontend_index = "/home/hn3t/workforce/frontend/dist/index.html"
    with open(frontend_index, "r") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.get("/roles/", response_class=HTMLResponse, include_in_schema=False)
def roles_ui(request: Request):
    return templates.TemplateResponse("roles.html", {"request": request})
