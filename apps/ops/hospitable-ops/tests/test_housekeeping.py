from apps.api.app.services.housekeeping import create_unit, create_task, transition_task
from apps.api.app.models.housekeeping_models import TaskStatus
from apps.api.app.services.rbac_service import init_db


def setup_module(module):
    init_db()


def test_unit_and_task_lifecycle():
    u = create_unit('loc-1', '101')
    assert u.label == '101'

    t = create_task('loc-1', u.id, '2026-03-03', 'checkout')
    assert t.status.name == 'OPEN'

    t_assigned = transition_task(t.id, TaskStatus.ASSIGNED)
    assert t_assigned is not None
    assert t_assigned.status.name == 'ASSIGNED'

    t_in_progress = transition_task(t.id, TaskStatus.IN_PROGRESS)
    assert t_in_progress is not None
    assert t_in_progress.status.name == 'IN_PROGRESS'

    t_completed = transition_task(t.id, TaskStatus.COMPLETED)
    assert t_completed is not None
    assert t_completed.status.name == 'COMPLETED'

    # verify TaskStatusEvent and AuditEvent were recorded
    events = get_task_events(t.id)
    assert len(events) >= 3
    assert events[-1].new_status == TaskStatus.COMPLETED.value

    # ensure an AuditEvent exists for the transition
    from apps.api.app.db.session import SessionLocal
    from apps.api.app.models.housekeeping_models import AuditEvent

    db = SessionLocal()
    try:
        audits = db.query(AuditEvent).filter_by(entity_type='task', entity_id=t.id).all()
        assert len(audits) >= 1
        assert audits[-1].action == 'status_transition'
    finally:
        db.close()
