from fastapi import APIRouter, HTTPException
from app.core.rbac import create_role, ROLES

router = APIRouter()

@router.post('/roles')
async def post_role(payload: dict):
    role_id = payload.get('id')
    name = payload.get('name')
    permissions = payload.get('permissions', [])
    if not role_id or not name:
        raise HTTPException(status_code=400, detail='id and name required')
    create_role(role_id, name, permissions)
    return {'status': 'ok'}
