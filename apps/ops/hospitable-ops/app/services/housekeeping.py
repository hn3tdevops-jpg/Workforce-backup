import uuid
from apps.api.app.db.session import SessionLocal
from apps.api.app.models.housekeeping_models import Unit, Task, TaskStatus, TaskStatusEvent, AuditEvent, ChecklistTemplate, ChecklistTemplateItem, ChecklistRun, ChecklistRunItem
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


def create_checklist_template(location_id: str, title: str, items: list, created_by: str = None):
    """Create a checklist template with items. items is a list of dicts with keys: label, required (optional), item_order (optional)"""
    db = SessionLocal()
    try:
        tid = str(uuid.uuid4())
        tpl = ChecklistTemplate(id=tid, location_id=location_id, title=title, created_by=created_by)
        db.add(tpl)
        for it in items:
            iid = str(uuid.uuid4())
            item = ChecklistTemplateItem(
                id=iid,
                template_id=tid,
                label=it.get('label'),
                required=it.get('required', True),
                item_order=it.get('item_order')
            )
            db.add(item)
        db.commit()
        db.refresh(tpl)
        return tpl
    finally:
        db.close()


def get_checklist_template(template_id: str):
    db = SessionLocal()
    try:
        tpl = db.get(ChecklistTemplate, template_id)
        if not tpl:
            return None
        items = db.query(ChecklistTemplateItem).filter_by(template_id=template_id).order_by(ChecklistTemplateItem.created_at).all()
        return {
            'template': tpl,
            'items': items,
        }
    finally:
        db.close()


def create_checklist_run_from_template(template_id: str, started_by: str = None):
    db = SessionLocal()
    try:
        tpl = db.get(ChecklistTemplate, template_id)
        if not tpl:
            return None
        run_id = str(uuid.uuid4())
        run = ChecklistRun(id=run_id, template_id=template_id, location_id=tpl.location_id, started_by=started_by)
        db.add(run)
        db.flush()
        items = db.query(ChecklistTemplateItem).filter_by(template_id=template_id).order_by(ChecklistTemplateItem.created_at).all()
        for it in items:
            ri = ChecklistRunItem(
                id=str(uuid.uuid4()),
                run_id=run_id,
                template_item_id=it.id,
                label=it.label
            )
            db.add(ri)
        db.commit()
        db.refresh(run)
        return run
    finally:
        db.close()


def get_checklist_run(run_id: str):
    db = SessionLocal()
    try:
        run = db.get(ChecklistRun, run_id)
        if not run:
            return None
        items = db.query(ChecklistRunItem).filter_by(run_id=run_id).order_by(ChecklistRunItem.created_at).all()
        return {
            'run': run,
            'items': items,
        }
    finally:
        db.close()

