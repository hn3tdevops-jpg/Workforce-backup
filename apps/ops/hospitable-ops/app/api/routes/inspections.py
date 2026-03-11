from fastapi import APIRouter, HTTPException
from apps.api.app.services.inspection import create_inspection
from apps.api.app.services.housekeeping import get_task_events

router = APIRouter()


@router.post('/tasks/{task_id}/inspect')
async def inspect_task(task_id: str, payload: dict):
    passed = payload.get('passed')
    if passed is None:
        raise HTTPException(status_code=400, detail='passed required')
    inspection, err = create_inspection(
        task_id=task_id,
        passed=bool(passed),
        notes=payload.get('notes'),
        created_by=payload.get('created_by'),
    )
    if err == 'task_not_found':
        raise HTTPException(status_code=404, detail='task not found')
    if err == 'task_not_completed':
        raise HTTPException(status_code=400, detail='task must be COMPLETED before inspection')
    return {'id': inspection.id, 'task_id': inspection.task_id, 'passed': inspection.passed,
            'notes': inspection.notes, 'created_by': inspection.created_by}


@router.get('/tasks/{task_id}/events')
async def task_events(task_id: str):
    events = get_task_events(task_id)
    return [
        {'id': e.id, 'task_id': e.task_id, 'old_status': e.old_status,
         'new_status': e.new_status, 'changed_by': e.changed_by,
         'timestamp': e.timestamp.isoformat() if e.timestamp else None}
        for e in events
    ]
