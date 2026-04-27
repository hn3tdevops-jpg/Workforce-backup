from fastapi import APIRouter, FastAPI

api_router = APIRouter()


def include_routers(app: FastAPI | APIRouter = api_router) -> None:
    """Dynamically import and include endpoint routers.

    This avoids importing endpoint modules at package import time which can
    trigger model imports and create import-order races during test
    collection. Tests call import_models() explicitly before creating app which
    ensures the DB metadata is ready.
    """
    # Imported locally to avoid top-level import side-effects.
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

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    app.include_router(bootstrap_router, prefix="/bootstrap", tags=["bootstrap"])
    app.include_router(rooms_router, prefix="/rooms", tags=["rooms"])
    app.include_router(users_router, prefix="/users", tags=["users"])
    app.include_router(employees_router, prefix="/employees", tags=["employees"])
    app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
    app.include_router(assignments_router, prefix="/assignments", tags=["assignments"])
    app.include_router(shifts_router, prefix="/shifts", tags=["shifts"])
    app.include_router(me_router, prefix="/me", tags=["me"])