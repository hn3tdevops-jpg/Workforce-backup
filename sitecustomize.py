"""
sitecustomize to alias apps.api.app.* modules to app.* module names to avoid duplicate
SQLAlchemy model registrations when tests import both namespaces.
This is a targeted, test-time compatibility shim only.
"""
import importlib
import sys

aliases = [
    'apps.api.app.models.base',
    'apps.api.app.models.user',
    'apps.api.app.models.tenant',
    'apps.api.app.models.access_control',
    'apps.api.app.services.rbac_service',
    'apps.api.app.services.rbac_seed_service',
    'apps.api.app.services.rbac_service',
    'apps.api.app.services.rbac_seed_service',
]

# Pre-import and alias modules so that both 'apps.api.app.*' and 'app.*' names resolve
for full in aliases:
    try:
        mod = importlib.import_module(full)
    except Exception:
        continue
    alt = full.replace('apps.api.app', 'app')
    # Register both module name variants to the same module object
    sys.modules[full] = mod
    sys.modules[alt] = mod

# Also alias the top-level package names
try:
    app_pkg = importlib.import_module('apps.api.app')
    sys.modules['app'] = app_pkg
    sys.modules['apps.api.app'] = app_pkg
except Exception:
    pass

# Ensure 'app.models' points to apps.api.app.models package if available
try:
    models_pkg = importlib.import_module('apps.api.app.models')
    sys.modules['app.models'] = models_pkg
    sys.modules['apps.api.app.models'] = models_pkg
except Exception:
    pass
