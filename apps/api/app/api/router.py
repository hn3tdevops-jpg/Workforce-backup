from fastapi import APIRouter

from apps.api.app.api.routes.bootstrap import router as bootstrap_router

api_router = APIRouter()
api_router.include_router(bootstrap_router, tags=["bootstrap"])
