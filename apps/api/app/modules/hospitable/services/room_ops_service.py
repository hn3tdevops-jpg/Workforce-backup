"""
Service layer for Hospitable / Silver Sands room operations.
All methods accept an AsyncSession and return ORM objects or dicts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from apps.api.app.modules.hospitable.models.property_ops import (
    HKRoom,
    HKRoomAsset,
    HKRoomStatusEvent,
    HKRoomSupplyPar,
    HKTask,
    HKTaskEvent,
    HousekeepingStatus,
    InspectionStatus,
    MaintenanceIssue,
    MaintenanceIssueStatus,
    MaintenanceStatus,
    OccupancyStatus,
    PropertyBuilding,
    PropertyFloor,
    TaskStatus,
)
from apps.api.app.modules.hospitable.schemas.room_ops import (
    BulkRoomStatusPatch,
    MaintenanceIssueCreate,
    MaintenanceIssuePatch,
    RoomCreate,
    RoomStatusPatch,
    TaskAssign,
    TaskCreate,
    TaskStatusPatch,
)


# ---------------------------------------------------------------------------
# Property tree
# ---------------------------------------------------------------------------

async def get_property_tree(db: AsyncSession, location_id: str) -> list[PropertyBuilding]:
    result = await db.execute(
        select(PropertyBuilding)
        .where(PropertyBuilding.location_id == location_id)
        .options(
            selectinload(PropertyBuilding.floors).selectinload(PropertyFloor.sectors)
        )
        .order_by(PropertyBuilding.sort_order)
    )
    return result.scalars().all()


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

async def list_rooms(
    db: AsyncSession,
    location_id: str,
    *,
    building_id: Optional[int] = None,
    floor_id: Optional[int] = None,
    sector_id: Optional[int] = None,
    room_group_id: Optional[int] = None,
    housekeeping_status: Optional[HousekeepingStatus] = None,
    occupancy_status: Optional[OccupancyStatus] = None,
    inspection_status: Optional[InspectionStatus] = None,
    maintenance_status: Optional[MaintenanceStatus] = None,
    include_inactive: bool = False,
) -> list[HKRoom]:
    q = select(HKRoom).where(HKRoom.location_id == location_id)
    if not include_inactive:
        q = q.where(HKRoom.is_active == True)  # noqa: E712
    if building_id is not None:
        q = q.where(HKRoom.building_id == building_id)
    if floor_id is not None:
        q = q.where(HKRoom.floor_id == floor_id)
    if sector_id is not None:
        q = q.where(HKRoom.sector_id == sector_id)
    if room_group_id is not None:
        q = q.where(HKRoom.room_group_id == room_group_id)
    if housekeeping_status is not None:
        q = q.where(HKRoom.housekeeping_status == housekeeping_status)
    if occupancy_status is not None:
        q = q.where(HKRoom.occupancy_status == occupancy_status)
    if inspection_status is not None:
        q = q.where(HKRoom.inspection_status == inspection_status)
    if maintenance_status is not None:
        q = q.where(HKRoom.maintenance_status == maintenance_status)
    q = q.order_by(HKRoom.room_number)
    result = await db.execute(q)
    return result.scalars().all()


async def get_room(db: AsyncSession, room_id: int) -> Optional[HKRoom]:
    result = await db.execute(
        select(HKRoom)
        .where(HKRoom.id == room_id)
        .options(
            selectinload(HKRoom.assets),
            selectinload(HKRoom.supply_pars),
        )
    )
    return result.scalar_one_or_none()


async def create_room(db: AsyncSession, payload: RoomCreate) -> HKRoom:
    room = HKRoom(**payload.model_dump())
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


async def patch_room_status(
    db: AsyncSession,
    room_id: int,
    patch: RoomStatusPatch,
    actor_user_id: Optional[str] = None,
) -> Optional[HKRoom]:
    room = await db.get(HKRoom, room_id)
    if not room:
        return None

    changes: dict[str, tuple] = {}

    if patch.housekeeping_status is not None and patch.housekeeping_status != room.housekeeping_status:
        changes["housekeeping_status"] = (room.housekeeping_status.value, patch.housekeeping_status.value)
        room.housekeeping_status = patch.housekeeping_status
        if patch.housekeeping_status == HousekeepingStatus.clean:
            room.last_cleaned_at = datetime.now(timezone.utc)
        if patch.housekeeping_status == HousekeepingStatus.inspected:
            room.last_inspected_at = datetime.now(timezone.utc)

    if patch.occupancy_status is not None and patch.occupancy_status != room.occupancy_status:
        changes["occupancy_status"] = (room.occupancy_status.value, patch.occupancy_status.value)
        room.occupancy_status = patch.occupancy_status

    if patch.inspection_status is not None and patch.inspection_status != room.inspection_status:
        changes["inspection_status"] = (room.inspection_status.value, patch.inspection_status.value)
        room.inspection_status = patch.inspection_status

    if patch.maintenance_status is not None and patch.maintenance_status != room.maintenance_status:
        changes["maintenance_status"] = (room.maintenance_status.value, patch.maintenance_status.value)
        room.maintenance_status = patch.maintenance_status

    if patch.out_of_order_reason is not None:
        room.out_of_order_reason = patch.out_of_order_reason

    if patch.notes is not None:
        room.notes = patch.notes

    # Log status events
    for field, (old_val, new_val) in changes.items():
        db.add(HKRoomStatusEvent(
            room_id=room_id,
            event_type=f"{field}_changed",
            old_value=old_val,
            new_value=new_val,
            created_by_user_id=actor_user_id,
        ))

    await db.commit()
    await db.refresh(room)
    return room


async def bulk_patch_room_status(
    db: AsyncSession,
    patch: BulkRoomStatusPatch,
    actor_user_id: Optional[str] = None,
) -> list[int]:
    updated_ids: list[int] = []
    for room_id in patch.room_ids:
        single = RoomStatusPatch(
            housekeeping_status=patch.housekeeping_status,
            occupancy_status=patch.occupancy_status,
            inspection_status=patch.inspection_status,
            maintenance_status=patch.maintenance_status,
            notes=patch.notes,
        )
        room = await patch_room_status(db, room_id, single, actor_user_id)
        if room:
            updated_ids.append(room_id)
    return updated_ids


# ---------------------------------------------------------------------------
# Room assets
# ---------------------------------------------------------------------------

async def list_room_assets(db: AsyncSession, room_id: int) -> list[HKRoomAsset]:
    result = await db.execute(
        select(HKRoomAsset).where(HKRoomAsset.room_id == room_id)
    )
    return result.scalars().all()


async def create_room_asset(
    db: AsyncSession, room_id: int, payload: dict
) -> HKRoomAsset:
    asset = HKRoomAsset(room_id=room_id, **payload)
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


# ---------------------------------------------------------------------------
# Supply pars
# ---------------------------------------------------------------------------

async def list_supply_pars(db: AsyncSession, room_id: int) -> list[HKRoomSupplyPar]:
    result = await db.execute(
        select(HKRoomSupplyPar).where(HKRoomSupplyPar.room_id == room_id)
    )
    return result.scalars().all()


async def create_supply_par(
    db: AsyncSession, room_id: int, payload: dict
) -> HKRoomSupplyPar:
    par = HKRoomSupplyPar(room_id=room_id, **payload)
    db.add(par)
    await db.commit()
    await db.refresh(par)
    return par


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

async def list_tasks(
    db: AsyncSession,
    location_id: str,
    *,
    status: Optional[TaskStatus] = None,
    room_id: Optional[int] = None,
    assigned_user_id: Optional[str] = None,
) -> list[HKTask]:
    q = select(HKTask).where(HKTask.location_id == location_id)
    if status is not None:
        q = q.where(HKTask.status == status)
    if room_id is not None:
        q = q.where(HKTask.room_id == room_id)
    if assigned_user_id is not None:
        q = q.where(HKTask.assigned_user_id == assigned_user_id)
    q = q.order_by(HKTask.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


async def create_task(db: AsyncSession, payload: TaskCreate) -> HKTask:
    task = HKTask(**payload.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def patch_task_status(
    db: AsyncSession,
    task_id: int,
    patch: TaskStatusPatch,
    actor_user_id: Optional[str] = None,
) -> Optional[HKTask]:
    task = await db.get(HKTask, task_id)
    if not task:
        return None

    old_status = task.status
    task.status = patch.status
    if patch.status == TaskStatus.done:
        task.completed_at = datetime.now(timezone.utc)

    db.add(HKTaskEvent(
        task_id=task_id,
        event_type="status_changed",
        from_status=old_status.value,
        to_status=patch.status.value,
        notes=patch.notes,
        created_by_user_id=actor_user_id,
    ))

    await db.commit()
    await db.refresh(task)
    return task


async def assign_task(
    db: AsyncSession,
    task_id: int,
    payload: TaskAssign,
    actor_user_id: Optional[str] = None,
) -> Optional[HKTask]:
    task = await db.get(HKTask, task_id)
    if not task:
        return None
    task.assigned_user_id = payload.assigned_user_id
    if task.status == TaskStatus.open:
        task.status = TaskStatus.assigned
        db.add(HKTaskEvent(
            task_id=task_id,
            event_type="assigned",
            from_status=TaskStatus.open.value,
            to_status=TaskStatus.assigned.value,
            created_by_user_id=actor_user_id,
        ))
    await db.commit()
    await db.refresh(task)
    return task


# ---------------------------------------------------------------------------
# Maintenance issues
# ---------------------------------------------------------------------------

async def list_maintenance_issues(
    db: AsyncSession,
    location_id: str,
    *,
    status: Optional[MaintenanceIssueStatus] = None,
    room_id: Optional[int] = None,
) -> list[MaintenanceIssue]:
    q = select(MaintenanceIssue).where(MaintenanceIssue.location_id == location_id)
    if status is not None:
        q = q.where(MaintenanceIssue.status == status)
    if room_id is not None:
        q = q.where(MaintenanceIssue.room_id == room_id)
    q = q.order_by(MaintenanceIssue.reported_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


async def create_maintenance_issue(
    db: AsyncSession,
    payload: MaintenanceIssueCreate,
    reporter_user_id: Optional[str] = None,
) -> MaintenanceIssue:
    issue = MaintenanceIssue(
        **payload.model_dump(),
        reported_by_user_id=reporter_user_id,
    )
    db.add(issue)
    await db.commit()
    await db.refresh(issue)
    return issue


async def patch_maintenance_issue(
    db: AsyncSession,
    issue_id: int,
    patch: MaintenanceIssuePatch,
) -> Optional[MaintenanceIssue]:
    issue = await db.get(MaintenanceIssue, issue_id)
    if not issue:
        return None
    for field, value in patch.model_dump(exclude_none=True).items():
        setattr(issue, field, value)
    await db.commit()
    await db.refresh(issue)
    return issue


# ---------------------------------------------------------------------------
# Dashboard summary
# ---------------------------------------------------------------------------

async def get_dashboard_summary(db: AsyncSession, location_id: str) -> dict:
    rooms_result = await db.execute(
        select(HKRoom).where(HKRoom.location_id == location_id, HKRoom.is_active == True)  # noqa: E712
    )
    rooms = rooms_result.scalars().all()

    total = len(rooms)
    dirty = sum(1 for r in rooms if r.housekeeping_status == HousekeepingStatus.dirty)
    assigned = sum(1 for r in rooms if r.housekeeping_status == HousekeepingStatus.assigned)
    cleaning = sum(1 for r in rooms if r.housekeeping_status == HousekeepingStatus.cleaning)
    clean = sum(1 for r in rooms if r.housekeeping_status == HousekeepingStatus.clean)
    inspect = sum(1 for r in rooms if r.housekeeping_status == HousekeepingStatus.inspect)
    inspected = sum(1 for r in rooms if r.housekeeping_status == HousekeepingStatus.inspected)
    blocked = sum(1 for r in rooms if r.housekeeping_status == HousekeepingStatus.blocked)
    maint_flagged = sum(1 for r in rooms if r.maintenance_status != MaintenanceStatus.ok)

    open_tasks_result = await db.execute(
        select(func.count(HKTask.id)).where(
            HKTask.location_id == location_id,
            HKTask.status.in_([TaskStatus.open, TaskStatus.assigned, TaskStatus.in_progress]),
        )
    )
    open_tasks = open_tasks_result.scalar_one()

    open_issues_result = await db.execute(
        select(func.count(MaintenanceIssue.id)).where(
            MaintenanceIssue.location_id == location_id,
            MaintenanceIssue.status.in_([
                MaintenanceIssueStatus.open,
                MaintenanceIssueStatus.triaged,
                MaintenanceIssueStatus.in_progress,
            ]),
        )
    )
    open_issues = open_issues_result.scalar_one()

    return {
        "location_id": location_id,
        "total_rooms": total,
        "dirty_rooms": dirty,
        "assigned_rooms": assigned,
        "cleaning_rooms": cleaning,
        "clean_rooms": clean,
        "inspect_rooms": inspect,
        "inspected_rooms": inspected,
        "blocked_rooms": blocked,
        "maintenance_flagged_rooms": maint_flagged,
        "open_tasks": open_tasks,
        "open_maintenance_issues": open_issues,
    }
