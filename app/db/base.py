from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_models() -> None:
    """Import all models so Alembic metadata is populated."""
    import app.models.tenant  # noqa: F401
    import app.models.user  # noqa: F401
