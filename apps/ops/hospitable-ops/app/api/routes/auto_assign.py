from fastapi import APIRouter, HTTPException
from apps.api.app.services.auto_assign import preview_auto_assign, execute_auto_assign

router = APIRouter()

@router.post('/locations/{location_id}/auto-assign/preview')
async def preview(location_id: str, payload: dict):
    date = payload.get('date')
    return preview_auto_assign(date, location_id)

@router.post('/locations/{location_id}/auto-assign/execute')
async def execute(location_id: str, payload: dict):
    assignments = payload.get('assignments')
    if not isinstance(assignments, list):
        raise HTTPException(status_code=400, detail='assignments list required')
    return execute_auto_assign(assignments)
