from typing import List, Dict
from apps.api.app.services.integrations_workforce import fetch_shifts
from apps.api.app.db.session import SessionLocal
from apps.api.app.models.integrations_models import ShiftRef

# Simple weighted round-robin by shift duration

def _compute_weights(shifts: List[Dict]) -> Dict[str, int]:
    weights = {}
    for s in shifts:
        eid = s.get('external_employee_id')
        start = s.get('start_at')
        end = s.get('end_at')
        duration = 1
        if start and end:
            try:
                duration = int((end - start).total_seconds() / 60)
            except Exception:
                duration = 1
        weights[eid] = weights.get(eid, 0) + max(duration, 1)
    return weights


def preview_auto_assign(date, location_id):
    # Fetch shifts and unassigned tasks (stubbed)
    shifts = fetch_shifts(date, location_id)
    # tasks should be fetched from tasks table; using placeholder
    tasks = []
    weights = _compute_weights(shifts)
    # simple assignment: round-robin by expanding weights
    pool = []
    for eid, w in weights.items():
        pool.extend([eid] * max(1, int(w / 30)))  # one slot per 30 minutes
    assignments = []
    for i, t in enumerate(tasks):
        if not pool:
            break
        assignee = pool[i % len(pool)]
        assignments.append({"task_id": t.get('id'), "proposed_assignee": assignee})
    return assignments


def execute_auto_assign(assignments: List[Dict]):
    db = SessionLocal()
    try:
        results = []
        for a in assignments:
            # In real system link task to external employee; here we return confirmation
            results.append({"task_id": a.get('task_id'), "assigned_to": a.get('proposed_assignee') or a.get('external_employee_id')})
        return results
    finally:
        db.close()
