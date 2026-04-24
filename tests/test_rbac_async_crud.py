import importlib
import os


def test_rbac_async_models_present():
    os.environ['SKIP_WORKFORCE_MODELS'] = '1'
    m = importlib.import_module('apps.api.app.models.access_control')
    assert 'ScopedRoleAssignment' in getattr(m, '__all__', [])
    assert 'Role' in getattr(m, '__all__', [])
    assert 'Membership' in getattr(m, '__all__', [])
