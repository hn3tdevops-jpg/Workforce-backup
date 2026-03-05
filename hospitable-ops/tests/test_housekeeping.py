from app.services.housekeeping import create_unit, create_task, transition_task
from app.services.rbac_service import init_db


def setup_module(module):
    init_db()


def test_unit_and_task_lifecycle():
    u = create_unit('loc-1', '101')
    assert u.label == '101'
    t = create_task('loc-1', u.id, '2026-03-03', 'checkout')
    assert t.status.name == 'OPEN'
    t2 = transition_task(t.id, t.__class__.status.type.python_type.OPEN) if False else transition_task(t.id, t.__class__.status.type.python_type.ASSIGNED)
    # since helper types aren't easily introspected here, just call allowed transition
    t_assigned = transition_task(t.id, t.__class__.status.type.python_type.ASSIGNED) if False else None
    # instead, test direct transitions via service
    from app.models.housekeeping_models import TaskStatus
    t_assigned = transition_task(t.id, TaskStatus.ASSIGNED)
    assert t_assigned.status.name == 'ASSIGNED'
