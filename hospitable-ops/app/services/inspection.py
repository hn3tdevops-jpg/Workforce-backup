import uuid
import json
from app.db.session import SessionLocal
from app.models.housekeeping_models import Inspection, Task, TaskStatus, AuditEvent
from app.services.housekeeping import transition_task


def create_inspection(task_id: str, passed: bool, notes: str = None, created_by: str = None):
    """
    Create an inspection record for a completed task.
    - Task must be in COMPLETED status.
    - If passed, transitions task to INSPECTED and inserts AuditEvent.
    - If not passed, leaves task in COMPLETED (reinspection/rework policy TBD).
    """
    db = SessionLocal()
    try:
        t = db.get(Task, task_id)
        if not t:
            return None, 'task_not_found'
        if t.status != TaskStatus.COMPLETED:
            return None, 'task_not_completed'

        inspection = Inspection(
            id=str(uuid.uuid4()),
            task_id=task_id,
            passed=passed,
            notes=notes,
            created_by=created_by,
        )
        db.add(inspection)

        audit = AuditEvent(
            id=str(uuid.uuid4()),
            location_id=t.location_id,
            actor_user_id=created_by,
            entity_type='inspection',
            entity_id=inspection.id,
            action='created',
            payload_json=json.dumps({'task_id': task_id, 'passed': passed}),
        )
        db.add(audit)
        db.commit()
        db.refresh(inspection)
    finally:
        db.close()

    if passed:
        transition_task(task_id, TaskStatus.INSPECTED, changed_by=created_by)

    return inspection, None
