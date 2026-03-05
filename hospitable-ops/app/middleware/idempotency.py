from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.services.idempotency import get_by_key, create_key_if_missing
import json

class IdempotencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        key = request.headers.get('X-Idempotency-Key')
        if not key:
            return await call_next(request)
        existing = get_by_key(key)
        if existing and existing.response_status is not None:
            body = existing.response_body_json or {"message": "replayed"}
            return Response(content=json.dumps(body), status_code=int(existing.response_status), media_type='application/json')
        # create placeholder so concurrent requests can detect in-flight
        create_key_if_missing(key, location_id=None, request_hash=None)
        return await call_next(request)
