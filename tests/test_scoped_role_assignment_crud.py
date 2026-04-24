import importlib
import os


def test_scoped_role_assignment_fields_present():
    os.environ['SKIP_WORKFORCE_MODELS'] = '1'
    m = importlib.import_module('apps.api.app.models.access_control')
    S = getattr(m, 'ScopedRoleAssignment', None)
    assert S is not None
    for attr in ('id','membership_id','role_id','location_id','created_at'):
        assert hasattr(S, attr)
