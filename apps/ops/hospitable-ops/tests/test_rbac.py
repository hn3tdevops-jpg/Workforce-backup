from apps.api.app.services.rbac_service import init_db, create_role, create_permission, add_permission_to_role, assign_role_to_user, get_user_permissions


def setup_module(module):
    init_db()


def test_role_permission_assignment():
    role = create_role('biz-1', 'BUSINESS', 'Manager')
    perm = create_permission('employees.read')
    assert perm.key == 'employees.read'
    added = add_permission_to_role(role.id, 'employees.read')
    assert added


def test_user_permissions():
    role = create_role('biz-1', 'BUSINESS', 'Cleaner')
    add_permission_to_role(role.id, 'housekeeping.tasks.assign')
    assignment = assign_role_to_user('user-1', 'biz-1', 'BUSINESS', role.id)
    perms = get_user_permissions('user-1')
    assert 'housekeeping.tasks.assign' in perms
