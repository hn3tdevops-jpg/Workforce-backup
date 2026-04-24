import importlib
import os


def test_tenant_crud_fields_present():
    os.environ['SKIP_WORKFORCE_MODELS'] = '1'
    m = importlib.import_module('apps.api.app.models.tenant_local')
    Tenant = getattr(m, 'Tenant', None)
    assert Tenant is not None
    # ensure key mapped attributes are present
    for attr in ('id','name','slug','settings_json','is_active','created_at'):
        assert hasattr(Tenant, attr)
