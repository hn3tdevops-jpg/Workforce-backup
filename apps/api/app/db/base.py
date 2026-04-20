# Import Base in a way that is robust to test sys.path manipulation.
# Prefer importing the canonical package path `apps.api.app` to avoid duplicate
# SQLAlchemy MetaData registrations when `app` alias modules exist.
try:
    from apps.api.app.models.base import Base  # type: ignore  # noqa: F401
    _use_app_pkg = False
except Exception:
    # Fallback for legacy tests that rely on top-level `app` package name
    from app.models.base import Base  # type: ignore  # noqa: F401
    _use_app_pkg = True

# Ensure sqlite accepts Python uuid.UUID objects by registering an adapter early
# This makes tests that construct model instances with uuid.UUID work with the
# in-memory sqlite driver used by the test harness.
try:
    import sqlite3
    import uuid as _uuid_module
    sqlite3.register_adapter(_uuid_module.UUID, lambda u: str(u))
except Exception:
    # Not critical; if sqlite isn't available or registration fails, continue.
    pass


def import_core_models() -> None:
    """Import core model modules, preferring canonical packages.workforce when available.

    This ensures SQLAlchemy metadata is populated from the canonical model
    implementations and avoids duplicate Table registrations from duplicate
    model definitions.
    """
    # Try canonical packaged models first, unless the test harness requests SKIP_WORKFORCE_MODELS
    import os
    if not os.environ.get('SKIP_WORKFORCE_MODELS'):
        try:
            # import canonical identity/business/employee models
            import importlib
            importlib.import_module('packages.workforce.workforce.app.models.identity')
            importlib.import_module('packages.workforce.workforce.app.models.business')
            importlib.import_module('packages.workforce.workforce.app.models.employee')
            return
        except Exception:
            # Fall back to local app package models
            pass

    if _use_app_pkg:
        import app.models.tenant  # noqa: F401
        import app.models.user  # noqa: F401
        import app.models.access_control  # noqa: F401
    else:
        import apps.api.app.models.tenant  # noqa: F401
        import apps.api.app.models.user  # noqa: F401
        import apps.api.app.models.access_control  # noqa: F401


def import_domain_models() -> None:
    if _use_app_pkg:
        import app.modules.hospitable.models.property_ops  # noqa: F401
    else:
        import apps.api.app.modules.hospitable.models.property_ops  # noqa: F401



def import_models(*args, **kwargs) -> None:
    """Import model modules.

    Accept arbitrary args/kwargs for compatibility with SQLAlchemy's
    Session.run_sync which forwards the session as the first positional
    argument.
    """
    import_core_models()
    import_domain_models()
