"""
Database base helpers.

import_models() ensures all ORM model modules are imported so that
SQLAlchemy's metadata and Alembic can see every table definition.
"""


def import_models() -> None:
    """Import all model modules to populate SQLAlchemy metadata."""
    import apps.api.app.models  # noqa: F401
    import apps.api.app.models.auth  # noqa: F401
