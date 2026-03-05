from fastapi import APIRouter, HTTPException
from app.services.integrations_workforce import upsert_employee_ref, upsert_shift_ref

router = APIRouter()

@router.post('/integrations/scheduling/employees.upsert')
async def employees_upsert(payload: dict):
    if not payload.get('location_id') or not payload.get('external_employee_id'):
        raise HTTPException(status_code=400, detail='location_id and external_employee_id required')
    upsert_employee_ref(payload)
    return {'status': 'ok'}

@router.post('/integrations/scheduling/shifts.upsert')
async def shifts_upsert(payload: dict):
    if not payload.get('location_id') or not payload.get('external_shift_id'):
        raise HTTPException(status_code=400, detail='location_id and external_shift_id required')
    upsert_shift_ref(payload)
    return {'status': 'ok'}

@router.get('/integrations/scheduling/health')
async def health():
    return {'status': 'ok'}
