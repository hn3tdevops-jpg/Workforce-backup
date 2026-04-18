from fastapi import APIRouter

from apps.api.app.api.v1.endpoints.assignments import router as assignments_router
from apps.api.app.api.v1.endpoints.auth import router as auth_router
from apps.api.app.api.v1.endpoints.bootstrap import router as bootstrap_router
from apps.api.app.api.v1.endpoints.health import router as health_router
from apps.api.app.api.v1.endpoints.rooms import router as rooms_router
from apps.api.app.api.v1.endpoints.users import router as users_router
from apps.api.app.api.v1.endpoints.shifts import router as shifts_router
from apps.api.app.api.v1.endpoints.tasks import router as tasks_router
from apps.api.app.api.v1.endpoints.me import router as me_router
from apps.api.app.api.v1.endpoints.employees import router as employees_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(bootstrap_router, prefix="/bootstrap", tags=["bootstrap"])
api_router.include_router(rooms_router, prefix="/rooms", tags=["rooms"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(employees_router, prefix="/employees", tags=["employees"])
api_router.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
api_router.include_router(assignments_router, prefix="/assignments", tags=["assignments"])
api_router.include_router(shifts_router, prefix="/shifts", tags=["shifts"])
api_router.include_router(me_router, prefix="/me", tags=["me"])