from fastapi import APIRouter

from apps.api.app.api.v1.endpoints import assignments, bootstrap, health, rooms, shifts, tasks
from apps.api.app.modules.hospitable.api.router import router as hospitable_router

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(bootstrap.router, prefix="/bootstrap", tags=["bootstrap"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["shifts"])
api_router.include_router(hospitable_router)
