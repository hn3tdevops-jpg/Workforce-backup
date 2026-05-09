import uuid
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.app.models.base import Base, UUIDMixin, TimestampMixin, UUIDString


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    business_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDString(),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=True,
    )

    memberships: Mapped[list["Membership"]] = relationship("Membership", back_populates="user")


__all__ = ["User"]
