from fastapi import APIRouter

"""
Provide lightweight stub router modules so importing from app.api.routes
succeeds when the full set of route modules are not present in this layout.
These stubs are intentionally minimal and safe for testing purposes.
"""

_dummy_router = APIRouter()

class _StubModule:
    def __init__(self, router: APIRouter):
        self.router = router

# Export names expected by downstream code (main apps may include these routers).
rbac = _StubModule(_dummy_router)
integrations = _StubModule(_dummy_router)
idempotency = _StubModule(_dummy_router)
auto_assign = _StubModule(_dummy_router)
housekeeping = _StubModule(_dummy_router)
me = _StubModule(_dummy_router)
inspections = _StubModule(_dummy_router)
issues = _StubModule(_dummy_router)
