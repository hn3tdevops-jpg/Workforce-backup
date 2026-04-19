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


def import_core_models() -> None:
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
