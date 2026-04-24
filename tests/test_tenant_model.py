import importlib
import os


def test_tenant_models_import():
    # Ensure fallback local models are exercised in test harness
    os.environ['SKIP_WORKFORCE_MODELS'] = '1'
    m = importlib.import_module('apps.api.app.models.tenant_local')
    assert 'Tenant' in getattr(m, '__all__', [])
    assert 'Business' in getattr(m, '__all__', [])
