from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from apps.api.app.api.routes import rbac, integrations, idempotency, auto_assign, housekeeping, me, inspections, issues
from apps.api.app.middleware.idempotency import IdempotencyMiddleware

app = FastAPI(title="hospitable-ops (skeleton)")
app.add_middleware(IdempotencyMiddleware)
app.include_router(rbac.router, prefix="/api/rbac")
app.include_router(integrations.router)
app.include_router(idempotency.router)
app.include_router(auto_assign.router)
app.include_router(housekeeping.router)
app.include_router(inspections.router)
app.include_router(issues.router)
app.include_router(me.router)

# Serve built frontend (if present) at /ui
_dist_dir = Path(__file__).resolve().parent.parent / 'frontend' / 'dist'
if _dist_dir.exists() and _dist_dir.is_dir():
    app.mount('/ui', StaticFiles(directory=str(_dist_dir), html=True), name='frontend')

@app.get("/")
async def root():
    return {"status": "ok", "service": "hospitable-ops"}

@app.get('/ui-status')
async def ui_status():
    index = _dist_dir / 'index.html'
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({'error': 'Built UI not found', 'build_path': str(_dist_dir)})
