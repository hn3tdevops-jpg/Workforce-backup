from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.api.app.api.router import api_router
from apps.api.app.db.base import import_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    import_models()
    yield


app = FastAPI(title="Workforce API", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")
