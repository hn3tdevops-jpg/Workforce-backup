import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def _sqlite_uuid_server_default():
    return text(
        "(lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || "
        "substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || "
        "substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))))"
    )


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=_sqlite_uuid_server_default(),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    settings_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())

    businesses: Mapped[list["Business"]] = relationship("Business", back_populates="tenant")


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=_sqlite_uuid_server_default(),
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    settings_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())

    tenant: Mapped["Tenant | None"] = relationship("Tenant", back_populates="businesses")
    locations: Mapped[list["Location"]] = relationship(
        "Location", back_populates="business", cascade="all, delete-orphan"
    )


class Location(Base):
    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        server_default=_sqlite_uuid_server_default(),
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    settings_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())

    business: Mapped["Business"] = relationship("Business", back_populates="locations")