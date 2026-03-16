from fastapi import APIRouter

api_router = APIRouter()

# Prefer importing auth and other v1 routers from the workforce package when available.
# Import in try/except blocks so the API can still start even if some modules are not present.
try:
    from apps.api.app.api.v1.auth import routes as auth_routes
    api_router.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
except Exception:
    # If the workforce v1.auth package isn't available, skip including auth routes.
    pass

# Include bootstrap if present
try:
    from apps.api.app.api.routes import bootstrap
    api_router.include_router(bootstrap.router)
except Exception:
    pass
