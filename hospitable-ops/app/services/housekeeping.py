import uuid
from app.db.session import SessionLocal
from app.models.housekeeping_models import Unit, Task, UnitStatus, TaskStatus
import datetime


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


def transition_task(task_id: str, new_status: TaskStatus):
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
        if t.status in allowed and new_status in allowed[t.status]:
            t.status = new_status
            if new_status == TaskStatus.IN_PROGRESS:
                t.started_at = datetime.datetime.utcnow()
            if new_status == TaskStatus.COMPLETED:
                t.completed_at = datetime.datetime.utcnow()
            db.add(t)
            db.commit()
            db.refresh(t)
            return t
        else:
            return None
    finally:
        db.close()
