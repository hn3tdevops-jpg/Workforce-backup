from app.models.base import Base


def import_core_models() -> None:
    """Import canonical core models so SQLAlchemy metadata is populated."""
    import app.models.tenant  # noqa: F401
    import app.models.user  # noqa: F401


def import_domain_models() -> None:
    """Import active domain models explicitly."""
    import app.modules.hospitable.models.property_ops  # noqa: F401


def import_models() -> None:
    """Import all currently active models."""
    import_core_models()
    import_domain_models()