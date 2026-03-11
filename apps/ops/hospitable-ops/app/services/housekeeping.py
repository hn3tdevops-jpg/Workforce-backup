import uuid
from apps.api.app.db.session import SessionLocal
from apps.api.app.models.housekeeping_models import Unit, Task, UnitStatus, TaskStatus, TaskStatusEvent, AuditEvent
import datetime
import json


def create_unit(location_id: str, label: str, type: str = None, notes: str = None):
    db = SessionLocal()
    try:
        u = Unit(id=str(uuid.uuid4()), location_id=location_id, label=label, type=type, notes=notes)
        db.add(u)
        db.commit()
        db.refresh(u)
        return u
    finally:
        db.close()


def create_task(location_id: str, unit_id: str, date: str, type: str):
    db = SessionLocal()
    try:
        t = Task(id=str(uuid.uuid4()), location_id=location_id, unit_id=unit_id, date=date, type=type)
        db.add(t)
        db.commit()
        db.refresh(t)
        return t
    finally:
        db.close()


def transition_task(task_id: str, new_status: TaskStatus, changed_by: str = None):
    db = SessionLocal()
    try:
        t = db.get(Task, task_id)
        if not t:
            return None
        # simple allowed transitions
        allowed = {
            TaskStatus.OPEN: [TaskStatus.ASSIGNED, TaskStatus.CANCELED],
            TaskStatus.ASSIGNED: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELED],
            TaskStatus.IN_PROGRESS: [TaskStatus.COMPLETED, TaskStatus.CANCELED],
            TaskStatus.COMPLETED: [TaskStatus.INSPECTED],
        }
        if t.status not in allowed or new_status not in allowed[t.status]:
            return None

        old_status = t.status
        t.status = new_status
        if new_status == TaskStatus.IN_PROGRESS:
            t.started_at = datetime.datetime.utcnow()
        if new_status == TaskStatus.COMPLETED:
            t.completed_at = datetime.datetime.utcnow()
        db.add(t)

        event = TaskStatusEvent(
            id=str(uuid.uuid4()),
            task_id=task_id,
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by=changed_by,
        )
        db.add(event)

        audit = AuditEvent(
            id=str(uuid.uuid4()),
            location_id=t.location_id,
            actor_user_id=changed_by,
            entity_type='task',
            entity_id=task_id,
            action='status_transition',
            payload_json=json.dumps({'old': old_status.value, 'new': new_status.value}),
        )
        db.add(audit)

        db.commit()
        db.refresh(t)
        return t
    finally:
        db.close()


def get_task_events(task_id: str):
    db = SessionLocal()
    try:
        return db.query(TaskStatusEvent).filter_by(task_id=task_id).order_by(TaskStatusEvent.timestamp).all()
    finally:
        db.close()
