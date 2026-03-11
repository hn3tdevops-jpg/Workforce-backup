from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.app.models.base import Base, TimestampMixin, UUIDMixin


class Business(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "businesses"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="free")
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    locations: Mapped[list["Location"]] = relationship("Location", back_populates="business")


class Location(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "locations"

    business_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    business: Mapped["Business"] = relationship("Business", back_populates="locations")
    parent: Mapped["Location | None"] = relationship(
        "Location", back_populates="children", remote_side="Location.id"
    )
    children: Mapped[list["Location"]] = relationship(
        "Location", back_populates="parent", cascade="all, delete-orphan"
    )
