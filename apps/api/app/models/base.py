import os

# Respect test harness opt-out for canonical packaged models
if not os.environ.get('SKIP_WORKFORCE_MODELS'):
    try:
        # Prefer the canonical packaged Base when available so all models share the same
        # DeclarativeBase/MetaData instance. This avoids cross-package duplicate
        # Table/ForeignKey resolution issues during the consolidation transition.
        from packages.workforce.workforce.app.models.base import (
            Base,
            TimestampMixin,
            UUIDMixin,
        )  # type: ignore
        _IMPORTED_CANONICAL = True
    except Exception:
        # Fall through to fallback below
        Base = None  # type: ignore
        _IMPORTED_CANONICAL = False
else:
    _IMPORTED_CANONICAL = False

if not _IMPORTED_CANONICAL or 'Base' not in globals() or getattr(globals().get('Base'), '__name__', None) is None:
    # Fallback: define a minimal compatible Base and mixins for environments
    # where the packaged workforce is not installed or test harness requests local models.
    import uuid
    from datetime import datetime, timezone

    from sqlalchemy import DateTime, String, func
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


    def _now() -> datetime:
        return datetime.now(timezone.utc)


    class Base(DeclarativeBase):
        """Canonical declarative base for the active Workforce backend."""
        pass


    class TimestampMixin:
        created_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), default=_now, nullable=False
        )
        updated_at: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), server_default=func.now(), default=_now, onupdate=_now, nullable=False
        )


    class UUIDMixin:
        id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

# Diagnostic: record Base.metadata identity
try:
    with open('/tmp/base_metadata_ids.log', 'a') as f:
        f.write(f"{__name__} BASE_METADATA_ID {id(Base.metadata)}\n")
except Exception:
    pass
