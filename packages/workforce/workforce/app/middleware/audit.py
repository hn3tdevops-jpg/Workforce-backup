"""
Audit middleware: attaches a correlation_id to every request,
and writes an AuditEvent for every mutating (non-GET) response.
"""
import uuid
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        response = await call_next(request)

        # Only audit mutations that succeeded (2xx)
        if request.method in MUTATION_METHODS and 200 <= response.status_code < 300:
            try:
                await _write_audit(request, response, correlation_id)
            except Exception:
                pass  # never let audit failure break the response

        response.headers["X-Correlation-ID"] = correlation_id
        return response


async def _write_audit(request: Request, response: Response, correlation_id: str):
    """Write an AuditEvent row for the request."""
    from apps.api.app.core.db import SessionLocal
    from apps.api.app.models.identity import ActorType, AuditEvent

    # Try to extract actor info from request state (set by auth deps)
    actor_type = ActorType.system
    actor_id: str | None = None
    business_id: str | None = None

    if hasattr(request.state, "current_user"):
        actor_type = ActorType.user
        actor_id = request.state.current_user.id
    elif hasattr(request.state, "current_agent"):
        actor_type = ActorType.agent
        actor_id = request.state.current_agent.id

    # Extract business_id from path
    path_parts = request.url.path.strip("/").split("/")
    for i, part in enumerate(path_parts):
        if part == "businesses" and i + 1 < len(path_parts):
            business_id = path_parts[i + 1]
            break

    # Derive entity + entity_id from path
    entity = path_parts[-2] if len(path_parts) >= 2 else "unknown"
    entity_id = path_parts[-1] if len(path_parts) >= 1 else "unknown"

    action = {
        "POST": "create",
        "PUT": "update",
        "PATCH": "patch",
        "DELETE": "delete",
    }.get(request.method, request.method.lower())

    db = SessionLocal()
    try:
        event = AuditEvent(
            business_id=business_id,
            actor_type=actor_type,
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            diff_json=None,
            correlation_id=correlation_id,
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
    finally:
        db.close()
