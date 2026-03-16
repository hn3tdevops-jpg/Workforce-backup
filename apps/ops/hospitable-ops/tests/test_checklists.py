from apps.api.app.services.rbac_service import init_db
from apps.api.app.services.housekeeping import (
    create_checklist_template,
    get_checklist_template,
    create_checklist_run_from_template,
    get_checklist_run,
)


def setup_module(module):
    init_db()


def test_checklist_template_and_run():
    items = [
        {'label': 'Make bed'},
        {'label': 'Empty trash', 'required': False},
    ]
    tpl = create_checklist_template('loc-1', 'Room clean', items, created_by='user-1')
    assert tpl is not None

    data = get_checklist_template(tpl.id)
    assert data['template'].title == 'Room clean'
    assert len(data['items']) == 2

    run = create_checklist_run_from_template(tpl.id, started_by='user-1')
    assert run is not None

    run_data = get_checklist_run(run.id)
    assert run_data['run'].template_id == tpl.id
    assert len(run_data['items']) == 2
