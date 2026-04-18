from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
    # Preferred import for older starlette versions
    from starlette.middleware.proxy_headers import ProxyHeadersMiddleware
except Exception:
    # Fallback shim for environments with newer starlette where proxy_headers module may be absent.
    # Provide a shim that accepts the same initialization kwargs (e.g. trusted_hosts) so
    # add_middleware() won't raise TypeError when it passes those kwargs.
    from starlette.middleware.base import BaseHTTPMiddleware

    class ProxyHeadersMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, trusted_hosts: str | None = "*", **kwargs):
            # BaseHTTPMiddleware expects only (app, dispatch=None)
            super().__init__(app)
            self.trusted_hosts = trusted_hosts

        async def dispatch(self, request, call_next):
            return await call_next(request)

from .api.router import api_router
from .db.base import import_models

# Ensure all SQLAlchemy models are registered before startup/migrations.
# import_models()  # deliberately not called at import time to avoid double-registration
# Tests call import_models() explicitly from conftest and the test harness controls DB lifecycle.


def get_cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ALLOW_ORIGINS", "").strip()
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    return [
        "https://hn3t.pythonanywhere.com",
        "https://wf-hn3t.pythonanywhere.com",
        "http://127.0.0.1:5000",
        "http://localhost:5000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://localhost:3000",
    ]


app = FastAPI(
    title="Workforce API",
    version="0.1.0",
)

# Respect X-Forwarded-* headers from reverse proxies (PythonAnywhere) so generated
# redirect Location headers preserve original scheme (https). Without this, the
# app may emit redirects to http://... which browsers treat as mixed-content and
# cause fetch to fail with "Failed to fetch" when the initial request was https.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["system"])
async def root() -> dict[str, str]:
    return {"message": "Workforce API is running"}


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router, prefix="/api/v1")