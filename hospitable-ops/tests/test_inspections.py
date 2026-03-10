from app.services.rbac_service import init_db
from app.services.housekeeping import create_unit, create_task, transition_task
from app.services.inspection import create_inspection
from app.models.housekeeping_models import TaskStatus


def setup_module(module):
    init_db()


def _make_completed_task():
    u = create_unit('loc-inspect', 'I101')
    t = create_task('loc-inspect', u.id, '2026-03-07', 'checkout')
    transition_task(t.id, TaskStatus.ASSIGNED)
    transition_task(t.id, TaskStatus.IN_PROGRESS)
    transition_task(t.id, TaskStatus.COMPLETED)
    return t


def test_inspection_pass_transitions_task():
    t = _make_completed_task()
    inspection, err = create_inspection(t.id, passed=True, notes='All good', created_by='inspector-1')
    assert err is None
    assert inspection is not None
    assert inspection.passed is True
    # Reload task via a fresh task lookup to verify INSPECTED
    from app.db.session import SessionLocal
    from app.models.housekeeping_models import Task
    db = SessionLocal()
    try:
        task = db.get(Task, t.id)
        assert task.status == TaskStatus.INSPECTED
    finally:
        db.close()


def test_inspection_fail_leaves_task_completed():
    t = _make_completed_task()
    inspection, err = create_inspection(t.id, passed=False, notes='Needs redo', created_by='inspector-1')
    assert err is None
    assert inspection is not None
    assert inspection.passed is False
    from app.db.session import SessionLocal
    from app.models.housekeeping_models import Task
    db = SessionLocal()
    try:
        task = db.get(Task, t.id)
        assert task.status == TaskStatus.COMPLETED
    finally:
        db.close()


def test_inspection_requires_completed_status():
    u = create_unit('loc-inspect', 'I102')
    t = create_task('loc-inspect', u.id, '2026-03-07', 'stayover')
    # Task is OPEN — should fail
    inspection, err = create_inspection(t.id, passed=True)
    assert inspection is None
    assert err == 'task_not_completed'


def test_inspection_task_not_found():
    inspection, err = create_inspection('nonexistent-task-id', passed=True)
    assert inspection is None
    assert err == 'task_not_found'
