"""
FastAPI router for the Hospitable / Silver Sands module.
Mounted at /api/v1/hospitable
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.session import get_async_session
from apps.api.app.modules.hospitable.models.property_ops import (
    HousekeepingStatus,
    InspectionStatus,
    MaintenanceIssueStatus,
    MaintenanceStatus,
    OccupancyStatus,
    PropertyBuilding,
    PropertyFloor,
    PropertySector,
    HKRoomGroup,
    TaskStatus,
)
from apps.api.app.modules.hospitable.schemas.room_ops import (
    BulkActionResult,
    BulkRoomStatusPatch,
    BuildingCreate,
    BuildingRead,
    FloorCreate,
    FloorRead,
    HousekeepingBoardEntry,
    MaintenanceBoardEntry,
    MaintenanceIssueCreate,
    MaintenanceIssuePatch,
    MaintenanceIssueRead,
    PropertyTree,
    PropertyTreeBuilding,
    PropertyTreeFloor,
    PropertyTreeSector,
    RoomAssetCreate,
    RoomAssetRead,
    RoomBoardSummary,
    RoomCreate,
    RoomGroupCreate,
    RoomGroupRead,
    RoomListItem,
    RoomRead,
    RoomStatusPatch,
    RoomSupplyParCreate,
    RoomSupplyParRead,
    SectorCreate,
    SectorRead,
    TaskAssign,
    TaskCreate,
    TaskRead,
    TaskStatusPatch,
)
from apps.api.app.modules.hospitable.services import room_ops_service as svc

router = APIRouter(prefix="/hospitable", tags=["hospitable"])


# ---------------------------------------------------------------------------
# Property structure
# ---------------------------------------------------------------------------

@router.get(
    "/locations/{location_id}/property-tree",
    response_model=PropertyTree,
    summary="Get full property hierarchy for a location",
)
async def get_property_tree(
    location_id: str,
    db: AsyncSession = Depends(get_async_session),
):
    buildings = await svc.get_property_tree(db, location_id)
    return PropertyTree(
        location_id=location_id,
        buildings=[
            PropertyTreeBuilding(
                id=b.id,
                code=b.code,
                name=b.name,
                sort_order=b.sort_order,
                is_active=b.is_active,
                floors=[
                    PropertyTreeFloor(
                        id=f.id,
                        floor_number=f.floor_number,
                        label=f.label,
                        sort_order=f.sort_order,
                        sectors=[
                            PropertyTreeSector(
                                id=s.id,
                                code=s.code,
                                name=s.name,
                                description=s.description,
                                sort_order=s.sort_order,
                            )
                            for s in sorted(f.sectors, key=lambda x: x.sort_order)
                        ],
                    )
                    for f in sorted(b.floors, key=lambda x: x.sort_order)
                ],
            )
            for b in buildings
        ],
    )


@router.post(
    "/buildings",
    response_model=BuildingRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a property building",
)
async def create_building(
    payload: BuildingCreate,
    db: AsyncSession = Depends(get_async_session),
):
    building = PropertyBuilding(**payload.model_dump())
    db.add(building)
    await db.commit()
    await db.refresh(building)
    return building


@router.post(
    "/floors",
    response_model=FloorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a property floor",
)
async def create_floor(
    payload: FloorCreate,
    db: AsyncSession = Depends(get_async_session),
):
    floor = PropertyFloor(**payload.model_dump())
    db.add(floor)
    await db.commit()
    await db.refresh(floor)
    return floor


@router.post(
    "/sectors",
    response_model=SectorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a property sector",
)
async def create_sector(
    payload: SectorCreate,
    db: AsyncSession = Depends(get_async_session),
):
    sector = PropertySector(**payload.model_dump())
    db.add(sector)
    await db.commit()
    await db.refresh(sector)
    return sector


@router.post(
    "/room-groups",
    response_model=RoomGroupRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a room group",
)
async def create_room_group(
    payload: RoomGroupCreate,
    db: AsyncSession = Depends(get_async_session),
):
    group = HKRoomGroup(**payload.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

@router.get(
    "/rooms",
    response_model=list[RoomListItem],
    summary="List rooms for a location with optional filters",
)
async def list_rooms(
    location_id: str = Query(...),
    building_id: Optional[int] = Query(None),
    floor_id: Optional[int] = Query(None),
    sector_id: Optional[int] = Query(None),
    room_group_id: Optional[int] = Query(None),
    housekeeping_status: Optional[HousekeepingStatus] = Query(None),
    occupancy_status: Optional[OccupancyStatus] = Query(None),
    inspection_status: Optional[InspectionStatus] = Query(None),
    maintenance_status: Optional[MaintenanceStatus] = Query(None),
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.list_rooms(
        db,
        location_id,
        building_id=building_id,
        floor_id=floor_id,
        sector_id=sector_id,
        room_group_id=room_group_id,
        housekeeping_status=housekeeping_status,
        occupancy_status=occupancy_status,
        inspection_status=inspection_status,
        maintenance_status=maintenance_status,
        include_inactive=include_inactive,
    )


@router.post(
    "/rooms",
    response_model=RoomRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new room",
)
async def create_room(
    payload: RoomCreate,
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.create_room(db, payload)


@router.get(
    "/rooms/{room_id}",
    response_model=RoomRead,
    summary="Get a single room with assets and supply pars",
)
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    room = await svc.get_room(db, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.patch(
    "/rooms/{room_id}/status",
    response_model=RoomListItem,
    summary="Update room status fields",
)
async def patch_room_status(
    room_id: int,
    patch: RoomStatusPatch,
    db: AsyncSession = Depends(get_async_session),
):
    room = await svc.patch_room_status(db, room_id, patch)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room


@router.post(
    "/rooms/bulk-status",
    response_model=BulkActionResult,
    summary="Bulk update housekeeping/occupancy status for multiple rooms",
)
async def bulk_room_status(
    patch: BulkRoomStatusPatch,
    db: AsyncSession = Depends(get_async_session),
):
    updated_ids = await svc.bulk_patch_room_status(db, patch)
    return BulkActionResult(updated_room_ids=updated_ids, count=len(updated_ids))


# ---------------------------------------------------------------------------
# Room assets
# ---------------------------------------------------------------------------

@router.get(
    "/rooms/{room_id}/assets",
    response_model=list[RoomAssetRead],
    summary="List assets for a room",
)
async def list_room_assets(
    room_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.list_room_assets(db, room_id)


@router.post(
    "/rooms/{room_id}/assets",
    response_model=RoomAssetRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add an asset to a room",
)
async def create_room_asset(
    room_id: int,
    payload: RoomAssetCreate,
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.create_room_asset(db, room_id, payload.model_dump())


# ---------------------------------------------------------------------------
# Supply pars
# ---------------------------------------------------------------------------

@router.get(
    "/rooms/{room_id}/supply-pars",
    response_model=list[RoomSupplyParRead],
    summary="List supply par levels for a room",
)
async def list_supply_pars(
    room_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.list_supply_pars(db, room_id)


@router.post(
    "/rooms/{room_id}/supply-pars",
    response_model=RoomSupplyParRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a supply par entry for a room",
)
async def create_supply_par(
    room_id: int,
    payload: RoomSupplyParCreate,
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.create_supply_par(db, room_id, payload.model_dump())


# ---------------------------------------------------------------------------
# Housekeeping tasks
# ---------------------------------------------------------------------------

@router.get(
    "/tasks",
    response_model=list[TaskRead],
    summary="List housekeeping tasks for a location",
)
async def list_tasks(
    location_id: str = Query(...),
    task_status: Optional[TaskStatus] = Query(None, alias="status"),
    room_id: Optional[int] = Query(None),
    assigned_user_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.list_tasks(
        db,
        location_id,
        status=task_status,
        room_id=room_id,
        assigned_user_id=assigned_user_id,
    )


@router.post(
    "/tasks",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a housekeeping task",
)
async def create_task(
    payload: TaskCreate,
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.create_task(db, payload)


@router.patch(
    "/tasks/{task_id}/status",
    response_model=TaskRead,
    summary="Update the status of a housekeeping task",
)
async def patch_task_status(
    task_id: int,
    patch: TaskStatusPatch,
    db: AsyncSession = Depends(get_async_session),
):
    task = await svc.patch_task_status(db, task_id, patch)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post(
    "/tasks/{task_id}/assign",
    response_model=TaskRead,
    summary="Assign a housekeeping task to an employee",
)
async def assign_task(
    task_id: int,
    payload: TaskAssign,
    db: AsyncSession = Depends(get_async_session),
):
    task = await svc.assign_task(db, task_id, payload)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post(
    "/tasks/{task_id}/complete",
    response_model=TaskRead,
    summary="Mark a housekeeping task as done",
)
async def complete_task(
    task_id: int,
    db: AsyncSession = Depends(get_async_session),
):
    patch = TaskStatusPatch(status=TaskStatus.done)
    task = await svc.patch_task_status(db, task_id, patch)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ---------------------------------------------------------------------------
# Maintenance issues
# ---------------------------------------------------------------------------

@router.get(
    "/maintenance/issues",
    response_model=list[MaintenanceIssueRead],
    summary="List maintenance issues for a location",
)
async def list_maintenance_issues(
    location_id: str = Query(...),
    issue_status: Optional[MaintenanceIssueStatus] = Query(None, alias="status"),
    room_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.list_maintenance_issues(
        db, location_id, status=issue_status, room_id=room_id
    )


@router.post(
    "/maintenance/issues",
    response_model=MaintenanceIssueRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a maintenance issue",
)
async def create_maintenance_issue(
    payload: MaintenanceIssueCreate,
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.create_maintenance_issue(db, payload)


@router.patch(
    "/maintenance/issues/{issue_id}",
    response_model=MaintenanceIssueRead,
    summary="Update a maintenance issue",
)
async def patch_maintenance_issue(
    issue_id: int,
    patch: MaintenanceIssuePatch,
    db: AsyncSession = Depends(get_async_session),
):
    issue = await svc.patch_maintenance_issue(db, issue_id, patch)
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    return issue


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@router.get(
    "/dashboard/summary",
    response_model=RoomBoardSummary,
    summary="Get operational dashboard summary for a location",
)
async def dashboard_summary(
    location_id: str = Query(...),
    db: AsyncSession = Depends(get_async_session),
):
    return await svc.get_dashboard_summary(db, location_id)


@router.get(
    "/dashboard/housekeeping-board",
    response_model=list[HousekeepingBoardEntry],
    summary="Get housekeeping task board for a location",
)
async def housekeeping_board(
    location_id: str = Query(...),
    db: AsyncSession = Depends(get_async_session),
):
    from sqlalchemy import select
    from apps.api.app.modules.hospitable.models.property_ops import HKTask, HKRoom
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(HKTask)
        .where(
            HKTask.location_id == location_id,
            HKTask.status.in_([TaskStatus.open, TaskStatus.assigned, TaskStatus.in_progress]),
        )
        .options(selectinload(HKTask.room))
        .order_by(HKTask.created_at.desc())
    )
    tasks = result.scalars().all()
    return [
        HousekeepingBoardEntry(
            id=t.id,
            room_id=t.room_id,
            room_number=t.room.room_number if t.room else None,
            task_type=t.task_type,
            title=t.title,
            priority=t.priority,
            status=t.status,
            assigned_user_id=t.assigned_user_id,
            due_at=t.due_at,
        )
        for t in tasks
    ]


@router.get(
    "/dashboard/maintenance-board",
    response_model=list[MaintenanceBoardEntry],
    summary="Get maintenance issue board for a location",
)
async def maintenance_board(
    location_id: str = Query(...),
    db: AsyncSession = Depends(get_async_session),
):
    from sqlalchemy import select
    from apps.api.app.modules.hospitable.models.property_ops import MaintenanceIssue, HKRoom
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(MaintenanceIssue)
        .where(
            MaintenanceIssue.location_id == location_id,
            MaintenanceIssue.status.in_([
                MaintenanceIssueStatus.open,
                MaintenanceIssueStatus.triaged,
                MaintenanceIssueStatus.in_progress,
            ]),
        )
        .options(selectinload(MaintenanceIssue.room))
        .order_by(MaintenanceIssue.reported_at.desc())
    )
    issues = result.scalars().all()
    return [
        MaintenanceBoardEntry(
            id=i.id,
            room_id=i.room_id,
            room_number=i.room.room_number if i.room else None,
            issue_type=i.issue_type,
            title=i.title,
            severity=i.severity,
            status=i.status,
            assigned_user_id=i.assigned_user_id,
            reported_at=i.reported_at,
        )
        for i in issues
    ]
