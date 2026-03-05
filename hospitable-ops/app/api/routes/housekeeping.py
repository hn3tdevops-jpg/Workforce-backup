from fastapi import APIRouter, HTTPException
from app.services.housekeeping import create_unit, create_task, transition_task
from app.models.housekeeping_models import TaskStatus

router = APIRouter()

@router.post('/locations/{location_id}/units')
async def post_unit(location_id: str, payload: dict):
    label = payload.get('label')
    if not label:
        raise HTTPException(status_code=400, detail='label required')
    return create_unit(location_id, label, payload.get('type'), payload.get('notes'))

@router.post('/locations/{location_id}/tasks')
async def post_task(location_id: str, payload: dict):
    unit_id = payload.get('unit_id')
    date = payload.get('date')
    ttype = payload.get('type')
    if not unit_id or not date or not ttype:
        raise HTTPException(status_code=400, detail='unit_id, date, type required')
    return create_task(location_id, unit_id, date, ttype)

@router.post('/tasks/{task_id}/status')
async def task_status(task_id: str, payload: dict):
    status = payload.get('status')
    if not status:
        raise HTTPException(status_code=400, detail='status required')
    try:
        new_status = TaskStatus[status]
    except Exception:
        raise HTTPException(status_code=400, detail='invalid status')
    t = transition_task(task_id, new_status)
    if not t:
        raise HTTPException(status_code=400, detail='invalid transition or task not found')
    return t
