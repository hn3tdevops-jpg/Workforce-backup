from apps.api.app.models.base import Base

def import_models() -> None:
    """Import all models so metadata is populated."""
    import apps.api.app.models.tenant  # noqa: F401
    import apps.api.app.models.user  # noqa: F401
    import apps.api.app.modules.hospitable.models.property_ops  # noqa: F401
