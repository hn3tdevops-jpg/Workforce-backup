from fastapi import APIRouter, HTTPException
from app.services.idempotency import get_by_key, store_response

router = APIRouter()

@router.get('/api/idempotency/keys/{key}')
async def get_key(key: str):
    ik = get_by_key(key)
    if not ik:
        raise HTTPException(status_code=404, detail='key not found')
    return {"key": ik.key, "response_status": ik.response_status, "response_body": ik.response_body_json}

@router.post('/api/idempotency/keys/{key}/store')
async def store_key_response(key: str, payload: dict):
    # payload: {status: int, body: object}
    status = payload.get('status')
    body = payload.get('body')
    if status is None:
        raise HTTPException(status_code=400, detail='status required')
    store_response(key, status, body)
    return {'status': 'ok'}
