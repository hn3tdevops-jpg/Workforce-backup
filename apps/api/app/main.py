from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from apps.api.app.db.base import import_models
from apps.api.app.api.router import api_router

# Register all models so SQLAlchemy metadata is fully populated
import_models()

app = FastAPI(title="Workforce API", version="0.1.0")

# Configure CORS origins via environment variable CORS_ALLOW_ORIGINS (comma-separated). If unset, use a conservative default list.
_orig = os.environ.get("CORS_ALLOW_ORIGINS")
if _orig:
    _orig_list = [o.strip() for o in _orig.split(",") if o.strip()]
else:
    _orig_list = [
        "https://hn3t.pythonanywhere.com",
        "http://127.0.0.1:5000",
        "http://localhost:5000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://localhost:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_orig_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("")
async def root() -> dict[str, str]:
    return {"message": "Workforce API is running"}

@app.get("/")
async def root_slash() -> dict[str, str]:
    return {"message": "Workforce API is running"}

app.include_router(api_router, prefix="/api/v1")
