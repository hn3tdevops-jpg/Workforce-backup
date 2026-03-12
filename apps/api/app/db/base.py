from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_models() -> None:
    """Import all models so Alembic metadata is populated."""
    import apps.api.app.models.tenant  # noqa: F401
    import apps.api.app.models.user  # noqa: F401
    import apps.api.app.modules.hospitable.models.property_ops  # noqa: F401
