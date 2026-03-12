"""
Pydantic v2 schemas for the Hospitable / Silver Sands module.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.modules.hospitable.models.property_ops import (
    FloorSurface,
    HousekeepingStatus,
    InspectionStatus,
    MaintenanceIssueStatus,
    MaintenanceStatus,
    OccupancyStatus,
    TaskPriority,
    TaskStatus,
    TaskType,
)


# ---------------------------------------------------------------------------
# Property hierarchy
# ---------------------------------------------------------------------------

class BuildingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    location_id: str
    code: str
    name: str
    sort_order: int
    is_active: bool


class BuildingCreate(BaseModel):
    location_id: str
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    sort_order: int = 0
    is_active: bool = True


class FloorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    building_id: int
    floor_number: int
    label: str
    sort_order: int


class FloorCreate(BaseModel):
    building_id: int
    floor_number: int
    label: str = Field(min_length=1, max_length=120)
    sort_order: int = 0


class SectorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    floor_id: int
    code: str
    name: str
    description: Optional[str] = None
    sort_order: int


class SectorCreate(BaseModel):
    floor_id: int
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = None
    sort_order: int = 0


class RoomGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    location_id: str
    name: str
    color: Optional[str] = None
    description: Optional[str] = None


class RoomGroupCreate(BaseModel):
    location_id: str
    name: str = Field(min_length=1, max_length=120)
    color: Optional[str] = None
    description: Optional[str] = None


# ---------------------------------------------------------------------------
# Property tree
# ---------------------------------------------------------------------------

class PropertyTreeSector(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    description: Optional[str] = None
    sort_order: int


class PropertyTreeFloor(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    floor_number: int
    label: str
    sort_order: int
    sectors: list[PropertyTreeSector] = []


class PropertyTreeBuilding(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    sort_order: int
    is_active: bool
    floors: list[PropertyTreeFloor] = []


class PropertyTree(BaseModel):
    location_id: str
    buildings: list[PropertyTreeBuilding] = []


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

class RoomAssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_type: str
    asset_name: str
    quantity_expected: int
    quantity_present: int
    condition_status: Optional[str] = None
    maintenance_notes: Optional[str] = None


class RoomAssetCreate(BaseModel):
    asset_type: str = Field(min_length=1, max_length=64)
    asset_name: str = Field(min_length=1, max_length=120)
    quantity_expected: int = 1
    quantity_present: int = 1
    condition_status: Optional[str] = None
    maintenance_notes: Optional[str] = None


class RoomSupplyParRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    item_code: str
    item_name: str
    expected_qty: int
    min_qty: int
    unit: str


class RoomSupplyParCreate(BaseModel):
    item_code: str = Field(min_length=1, max_length=64)
    item_name: str = Field(min_length=1, max_length=120)
    expected_qty: int
    min_qty: int
    unit: str = "ea"


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    location_id: str
    building_id: int
    floor_id: int
    sector_id: int
    room_group_id: Optional[int] = None
    room_number: str
    room_label: Optional[str] = None
    room_type: Optional[str] = None
    bed_count: Optional[int] = None
    bed_type_summary: Optional[str] = None
    floor_surface: FloorSurface
    housekeeping_status: HousekeepingStatus
    occupancy_status: OccupancyStatus
    inspection_status: InspectionStatus
    maintenance_status: MaintenanceStatus
    out_of_order_reason: Optional[str] = None
    notes: Optional[str] = None
    last_cleaned_at: Optional[datetime] = None
    last_inspected_at: Optional[datetime] = None
    is_active: bool
    assets: list[RoomAssetRead] = []
    supply_pars: list[RoomSupplyParRead] = []


class RoomListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    room_number: str
    room_label: Optional[str] = None
    room_type: Optional[str] = None
    housekeeping_status: HousekeepingStatus
    occupancy_status: OccupancyStatus
    inspection_status: InspectionStatus
    maintenance_status: MaintenanceStatus
    building_id: int
    floor_id: int
    sector_id: int
    room_group_id: Optional[int] = None
    is_active: bool


class RoomCreate(BaseModel):
    location_id: str
    building_id: int
    floor_id: int
    sector_id: int
    room_group_id: Optional[int] = None
    room_number: str = Field(min_length=1, max_length=16)
    room_label: Optional[str] = None
    room_type: Optional[str] = None
    bed_count: Optional[int] = None
    bed_type_summary: Optional[str] = None
    floor_surface: FloorSurface = FloorSurface.carpet
    notes: Optional[str] = None


class RoomStatusPatch(BaseModel):
    housekeeping_status: Optional[HousekeepingStatus] = None
    occupancy_status: Optional[OccupancyStatus] = None
    inspection_status: Optional[InspectionStatus] = None
    maintenance_status: Optional[MaintenanceStatus] = None
    out_of_order_reason: Optional[str] = None
    notes: Optional[str] = None


class BulkRoomStatusPatch(BaseModel):
    room_ids: list[int] = Field(min_length=1)
    housekeeping_status: Optional[HousekeepingStatus] = None
    occupancy_status: Optional[OccupancyStatus] = None
    inspection_status: Optional[InspectionStatus] = None
    maintenance_status: Optional[MaintenanceStatus] = None
    notes: Optional[str] = None


class BulkActionResult(BaseModel):
    updated_room_ids: list[int]
    count: int


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

class TaskCreate(BaseModel):
    location_id: str
    room_id: Optional[int] = None
    task_type: TaskType
    title: str = Field(min_length=1, max_length=160)
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.normal
    assigned_user_id: Optional[str] = None
    due_at: Optional[datetime] = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    location_id: str
    room_id: Optional[int] = None
    task_type: TaskType
    title: str
    description: Optional[str] = None
    priority: TaskPriority
    status: TaskStatus
    assigned_user_id: Optional[str] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TaskStatusPatch(BaseModel):
    status: TaskStatus
    notes: Optional[str] = None


class TaskAssign(BaseModel):
    assigned_user_id: str


# ---------------------------------------------------------------------------
# Maintenance issues
# ---------------------------------------------------------------------------

class MaintenanceIssueCreate(BaseModel):
    location_id: str
    room_id: Optional[int] = None
    issue_type: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=160)
    description: Optional[str] = None
    severity: str = "normal"
    assigned_user_id: Optional[str] = None


class MaintenanceIssueRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    location_id: str
    room_id: Optional[int] = None
    issue_type: str
    title: str
    description: Optional[str] = None
    severity: str
    status: MaintenanceIssueStatus
    assigned_user_id: Optional[str] = None
    reported_by_user_id: Optional[str] = None
    reported_at: datetime
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class MaintenanceIssuePatch(BaseModel):
    status: Optional[MaintenanceIssueStatus] = None
    severity: Optional[str] = None
    assigned_user_id: Optional[str] = None
    description: Optional[str] = None
    resolved_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class RoomBoardSummary(BaseModel):
    location_id: str
    total_rooms: int
    dirty_rooms: int
    assigned_rooms: int
    cleaning_rooms: int
    clean_rooms: int
    inspect_rooms: int
    inspected_rooms: int
    blocked_rooms: int
    maintenance_flagged_rooms: int
    open_tasks: int
    open_maintenance_issues: int


class HousekeepingBoardEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    room_id: Optional[int]
    room_number: Optional[str] = None
    task_type: TaskType
    title: str
    priority: TaskPriority
    status: TaskStatus
    assigned_user_id: Optional[str] = None
    due_at: Optional[datetime] = None


class MaintenanceBoardEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    room_id: Optional[int]
    room_number: Optional[str] = None
    issue_type: str
    title: str
    severity: str
    status: MaintenanceIssueStatus
    assigned_user_id: Optional[str] = None
    reported_at: datetime
