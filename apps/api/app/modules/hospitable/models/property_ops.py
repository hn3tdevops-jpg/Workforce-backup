"""
Hospitable / Silver Sands property operations models.
Integrated into the main Workforce apps/api codebase.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class HousekeepingStatus(str, enum.Enum):
    dirty = "dirty"
    assigned = "assigned"
    cleaning = "cleaning"
    clean = "clean"
    inspect = "inspect"
    inspected = "inspected"
    blocked = "blocked"


class OccupancyStatus(str, enum.Enum):
    vacant = "vacant"
    occupied = "occupied"
    checkout = "checkout"
    stayover = "stayover"
    ooo = "ooo"


class InspectionStatus(str, enum.Enum):
    not_required = "not_required"
    pending = "pending"
    passed = "passed"
    failed = "failed"


class MaintenanceStatus(str, enum.Enum):
    ok = "ok"
    issue = "issue"
    in_progress = "in_progress"
    resolved = "resolved"


class FloorSurface(str, enum.Enum):
    carpet = "carpet"
    hardwood = "hardwood"
    mixed = "mixed"
    tile = "tile"


class TaskType(str, enum.Enum):
    clean_checkout = "clean_checkout"
    clean_stayover = "clean_stayover"
    inspection = "inspection"
    restock = "restock"
    maintenance_followup = "maintenance_followup"


class TaskPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


class TaskStatus(str, enum.Enum):
    open = "open"
    assigned = "assigned"
    in_progress = "in_progress"
    done = "done"
    cancelled = "cancelled"


class MaintenanceIssueStatus(str, enum.Enum):
    open = "open"
    triaged = "triaged"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Property hierarchy
# ---------------------------------------------------------------------------

class PropertyBuilding(TimestampMixin, Base):
    __tablename__ = "property_buildings"
    __table_args__ = (
        UniqueConstraint("location_id", "code", name="uq_property_building_location_code"),
        Index("ix_property_buildings_location_id", "location_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    floors: Mapped[list["PropertyFloor"]] = relationship(
        back_populates="building", cascade="all, delete-orphan"
    )
    rooms: Mapped[list["HKRoom"]] = relationship(back_populates="building")


class PropertyFloor(TimestampMixin, Base):
    __tablename__ = "property_floors"
    __table_args__ = (
        UniqueConstraint("building_id", "floor_number", name="uq_property_floor_building_number"),
        Index("ix_property_floors_building_id", "building_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    building_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("property_buildings.id", ondelete="CASCADE"), nullable=False
    )
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    building: Mapped["PropertyBuilding"] = relationship(back_populates="floors")
    sectors: Mapped[list["PropertySector"]] = relationship(
        back_populates="floor", cascade="all, delete-orphan"
    )
    rooms: Mapped[list["HKRoom"]] = relationship(back_populates="floor")


class PropertySector(TimestampMixin, Base):
    __tablename__ = "property_sectors"
    __table_args__ = (
        UniqueConstraint("floor_id", "code", name="uq_property_sector_floor_code"),
        Index("ix_property_sectors_floor_id", "floor_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    floor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("property_floors.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    floor: Mapped["PropertyFloor"] = relationship(back_populates="sectors")
    rooms: Mapped[list["HKRoom"]] = relationship(back_populates="sector")


# ---------------------------------------------------------------------------
# Room groups
# ---------------------------------------------------------------------------

class HKRoomGroup(TimestampMixin, Base):
    __tablename__ = "hk_room_groups"
    __table_args__ = (Index("ix_hk_room_groups_location_id", "location_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    rooms: Mapped[list["HKRoom"]] = relationship(back_populates="room_group")


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

class HKRoom(TimestampMixin, Base):
    __tablename__ = "hk_rooms"
    __table_args__ = (
        UniqueConstraint("location_id", "room_number", name="uq_hk_room_location_number"),
        Index("ix_hk_rooms_location_id", "location_id"),
        Index("ix_hk_rooms_housekeeping_status", "housekeeping_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    building_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("property_buildings.id", ondelete="CASCADE"), nullable=False
    )
    floor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("property_floors.id", ondelete="CASCADE"), nullable=False
    )
    sector_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("property_sectors.id", ondelete="CASCADE"), nullable=False
    )
    room_group_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("hk_room_groups.id", ondelete="SET NULL"), nullable=True
    )
    room_number: Mapped[str] = mapped_column(String(16), nullable=False)
    room_label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    room_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    bed_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bed_type_summary: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    floor_surface: Mapped[FloorSurface] = mapped_column(
        Enum(FloorSurface), default=FloorSurface.carpet, nullable=False
    )
    housekeeping_status: Mapped[HousekeepingStatus] = mapped_column(
        Enum(HousekeepingStatus), default=HousekeepingStatus.dirty, nullable=False
    )
    occupancy_status: Mapped[OccupancyStatus] = mapped_column(
        Enum(OccupancyStatus), default=OccupancyStatus.vacant, nullable=False
    )
    inspection_status: Mapped[InspectionStatus] = mapped_column(
        Enum(InspectionStatus), default=InspectionStatus.not_required, nullable=False
    )
    maintenance_status: Mapped[MaintenanceStatus] = mapped_column(
        Enum(MaintenanceStatus), default=MaintenanceStatus.ok, nullable=False
    )
    out_of_order_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_cleaned_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_inspected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    building: Mapped["PropertyBuilding"] = relationship(back_populates="rooms")
    floor: Mapped["PropertyFloor"] = relationship(back_populates="rooms")
    sector: Mapped["PropertySector"] = relationship(back_populates="rooms")
    room_group: Mapped[Optional["HKRoomGroup"]] = relationship(back_populates="rooms")
    assets: Mapped[list["HKRoomAsset"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    supply_pars: Mapped[list["HKRoomSupplyPar"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["HKTask"]] = relationship(back_populates="room")
    maintenance_issues: Mapped[list["MaintenanceIssue"]] = relationship(back_populates="room")
    status_events: Mapped[list["HKRoomStatusEvent"]] = relationship(
        back_populates="room", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Room assets and supply pars
# ---------------------------------------------------------------------------

class HKRoomAsset(TimestampMixin, Base):
    __tablename__ = "hk_room_assets"
    __table_args__ = (Index("ix_hk_room_assets_room_id", "room_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hk_rooms.id", ondelete="CASCADE"), nullable=False
    )
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_name: Mapped[str] = mapped_column(String(120), nullable=False)
    quantity_expected: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    quantity_present: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    condition_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    maintenance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    room: Mapped["HKRoom"] = relationship(back_populates="assets")


class HKRoomSupplyPar(TimestampMixin, Base):
    __tablename__ = "hk_room_supply_pars"
    __table_args__ = (Index("ix_hk_room_supply_pars_room_id", "room_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hk_rooms.id", ondelete="CASCADE"), nullable=False
    )
    item_code: Mapped[str] = mapped_column(String(64), nullable=False)
    item_name: Mapped[str] = mapped_column(String(120), nullable=False)
    expected_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    min_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), default="ea", nullable=False)

    room: Mapped["HKRoom"] = relationship(back_populates="supply_pars")


# ---------------------------------------------------------------------------
# Housekeeping tasks
# ---------------------------------------------------------------------------

class HKTask(TimestampMixin, Base):
    __tablename__ = "hk_tasks"
    __table_args__ = (
        Index("ix_hk_tasks_location_id", "location_id"),
        Index("ix_hk_tasks_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("hk_rooms.id", ondelete="SET NULL"), nullable=True
    )
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority), default=TaskPriority.normal, nullable=False
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.open, nullable=False
    )
    assigned_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)

    room: Mapped[Optional["HKRoom"]] = relationship(back_populates="tasks")
    events: Mapped[list["HKTaskEvent"]] = relationship(
        back_populates="task", cascade="all, delete-orphan"
    )


class HKTaskEvent(Base):
    __tablename__ = "hk_task_events"
    __table_args__ = (Index("ix_hk_task_events_task_id", "task_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hk_tasks.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    from_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    to_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    task: Mapped["HKTask"] = relationship(back_populates="events")


# ---------------------------------------------------------------------------
# Maintenance issues
# ---------------------------------------------------------------------------

class MaintenanceIssue(TimestampMixin, Base):
    __tablename__ = "maintenance_issues"
    __table_args__ = (
        Index("ix_maintenance_issues_location_id", "location_id"),
        Index("ix_maintenance_issues_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("hk_rooms.id", ondelete="SET NULL"), nullable=True
    )
    issue_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(32), default="normal", nullable=False)
    status: Mapped[MaintenanceIssueStatus] = mapped_column(
        Enum(MaintenanceIssueStatus), default=MaintenanceIssueStatus.open, nullable=False
    )
    assigned_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    reported_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    room: Mapped[Optional["HKRoom"]] = relationship(back_populates="maintenance_issues")


# ---------------------------------------------------------------------------
# Room status events (audit log)
# ---------------------------------------------------------------------------

class HKRoomStatusEvent(Base):
    __tablename__ = "hk_room_status_events"
    __table_args__ = (Index("ix_hk_room_status_events_room_id", "room_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hk_rooms.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    room: Mapped["HKRoom"] = relationship(back_populates="status_events")
