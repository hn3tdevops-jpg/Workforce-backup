import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, func, text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
    from app.models.base import Base  # type: ignore
except Exception:
    from apps.api.app.models.base import Base  # type: ignore


def _sqlite_uuid_server_default():
    return text(
        "(lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || "
        "substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || "
        "substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))))"
    )


class UserEmployeeLink(Base):
    __tablename__ = "user_employee_links"
    __table_args__ = (
        UniqueConstraint("user_id", "employee_id", name="uq_user_employee_link"),
        Index("ix_uel_user_id", "user_id"),
        Index("ix_uel_employee_id", "employee_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=_sqlite_uuid_server_default(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employee_profiles.id", ondelete="CASCADE"), nullable=False
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    employee = relationship("EmployeeProfile", foreign_keys=[employee_id])
    business = relationship("Business")
