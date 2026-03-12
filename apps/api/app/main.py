from fastapi import FastAPI
from apps.api.app.db.base import import_models
from apps.api.app.api.router import api_router

# Register all models so SQLAlchemy metadata is fully populated
import_models()

app = FastAPI(title="Workforce API", version="0.1.0")

@app.get("")
async def root() -> dict[str, str]:
    return {"message": "Workforce API is running"}

@app.get("/")
async def root_slash() -> dict[str, str]:
    return {"message": "Workforce API is running"}

app.include_router(api_router, prefix="/api/v1")
