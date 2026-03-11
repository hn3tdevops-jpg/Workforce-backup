from fastapi import APIRouter, HTTPException
from apps.api.app.services.issue import create_issue, transition_issue
from apps.api.app.models.housekeeping_models import IssueStatus

router = APIRouter()


@router.post('/locations/{location_id}/issues')
async def post_issue(location_id: str, payload: dict):
    unit_id = payload.get('unit_id')
    if not unit_id:
        raise HTTPException(status_code=400, detail='unit_id required')
    issue, err = create_issue(
        location_id=location_id,
        unit_id=unit_id,
        category=payload.get('category'),
        severity=payload.get('severity'),
        description=payload.get('description'),
        created_by=payload.get('created_by'),
    )
    if err:
        raise HTTPException(status_code=400, detail=err)
    return {'id': issue.id, 'location_id': issue.location_id, 'unit_id': issue.unit_id,
            'category': issue.category, 'severity': issue.severity,
            'description': issue.description, 'status': issue.status.value}


@router.patch('/issues/{issue_id}')
async def patch_issue(issue_id: str, payload: dict):
    status_val = payload.get('status')
    if not status_val:
        raise HTTPException(status_code=400, detail='status required')
    try:
        new_status = IssueStatus[status_val]
    except KeyError:
        raise HTTPException(status_code=400, detail='invalid status')
    issue, err = transition_issue(issue_id, new_status, actor_user_id=payload.get('actor_user_id'))
    if err == 'issue_not_found':
        raise HTTPException(status_code=404, detail='issue not found')
    if err == 'invalid_transition':
        raise HTTPException(status_code=400, detail='invalid status transition')
    return {'id': issue.id, 'status': issue.status.value, 'updated_at': issue.updated_at.isoformat() if issue.updated_at else None}
