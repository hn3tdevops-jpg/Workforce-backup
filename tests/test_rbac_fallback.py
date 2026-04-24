import importlib
import os


def test_access_control_fallback():
    # Ensure local RBAC models load when SKIP_WORKFORCE_MODELS is set
    os.environ['SKIP_WORKFORCE_MODELS'] = '1'
    m = importlib.import_module('apps.api.app.models.access_control')
    assert 'Membership' in getattr(m, '__all__', [])
    assert 'Role' in getattr(m, '__all__', [])
