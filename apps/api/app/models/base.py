"""Compatibility shim: expose Base for alembic env imports.

Prefer the workforce models.Base when available so that all model classes
share the same DeclarativeBase and metadata during tests.
"""
try:
    # If the larger workforce package is present, prefer its Base so that
    # Base.metadata contains all tables defined in workforce models.
    from packages.workforce.workforce.app.models.base import Base  # type: ignore
    # Ensure all workforce models are imported so that Base.metadata is populated.
    try:
        import importlib, os, pkgutil
        pkg = importlib.import_module('packages.workforce.workforce.app.models')
        # Use pkgutil.iter_modules to reliably discover modules in package path
        for finder, name, ispkg in pkgutil.iter_modules(pkg.__path__):
            if name.startswith('__'):
                continue
            importlib.import_module(f'packages.workforce.workforce.app.models.{name}')
    except Exception:
        # Import failures should not crash test setup; fall back to local Base below
        pass
except Exception:
    from apps.api.app.db.base import Base  # type: ignore  # noqa: F401
