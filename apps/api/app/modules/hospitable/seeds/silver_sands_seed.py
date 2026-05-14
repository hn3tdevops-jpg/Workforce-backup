"""
Silver Sands Motel — location seed script.

Seeds:
  - Business: Silver Sands Motel
  - Location: Silver Sands Main Property
  - Building 1 / Floor 1 / North Sector / South Sector
  - North Group (rooms 7-12) / South Group (rooms 1-6)
  - 12 rooms with starter asset and supply par templates

Usage (from repo root):
    python -m apps.api.app.modules.hospitable.seeds.silver_sands_seed
"""
from __future__ import annotations

import asyncio
import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.app.modules.hospitable.models.property_ops import (
    FloorSurface,
    HKRoom,
    HKRoomAsset,
    HKRoomGroup,
    HKRoomSupplyPar,
    PropertyBuilding,
    PropertyFloor,
    PropertySector,
)
from apps.api.app.models.tenant import Business, Location

log = logging.getLogger(__name__)

STARTER_ASSETS = [
    {"asset_type": "tv", "asset_name": "Television", "quantity_expected": 1, "quantity_present": 1},
    {"asset_type": "fridge", "asset_name": "Mini Fridge", "quantity_expected": 1, "quantity_present": 1},
    {"asset_type": "microwave", "asset_name": "Microwave", "quantity_expected": 1, "quantity_present": 1},
    {"asset_type": "coffee_maker", "asset_name": "Coffee Maker", "quantity_expected": 1, "quantity_present": 1},
    {"asset_type": "hvac", "asset_name": "Heater / AC Unit", "quantity_expected": 1, "quantity_present": 1},
]

STARTER_SUPPLY_PARS = [
    {"item_code": "towel_bath", "item_name": "Bath Towels", "expected_qty": 4, "min_qty": 2, "unit": "ea"},
    {"item_code": "towel_hand", "item_name": "Hand Towels", "expected_qty": 4, "min_qty": 2, "unit": "ea"},
    {"item_code": "towel_wash", "item_name": "Washcloths", "expected_qty": 4, "min_qty": 2, "unit": "ea"},
    {"item_code": "sheet_flat", "item_name": "Flat Sheets", "expected_qty": 2, "min_qty": 1, "unit": "ea"},
    {"item_code": "sheet_fitted", "item_name": "Fitted Sheets", "expected_qty": 2, "min_qty": 1, "unit": "ea"},
    {"item_code": "pillowcase", "item_name": "Pillowcases", "expected_qty": 4, "min_qty": 2, "unit": "ea"},
    {"item_code": "blanket", "item_name": "Blankets", "expected_qty": 2, "min_qty": 1, "unit": "ea"},
    {"item_code": "trash_bag", "item_name": "Trash Bags", "expected_qty": 3, "min_qty": 1, "unit": "ea"},
    {"item_code": "soap_bar", "item_name": "Bar Soap", "expected_qty": 4, "min_qty": 2, "unit": "ea"},
    {"item_code": "shampoo", "item_name": "Shampoo", "expected_qty": 2, "min_qty": 1, "unit": "bottle"},
]


async def seed_silver_sands(
    session: AsyncSession,
    location_id: Optional[str] = None,
    business_id: Optional[str] = None,
) -> dict:
    """Seed the Silver Sands layout into the database."""
    if not location_id:
        biz_id = uuid.UUID(business_id) if business_id else uuid.uuid4()
        loc_id = uuid.uuid4()

        biz = Business(id=biz_id, name="Silver Sands Motel")
        session.add(biz)
        await session.flush()

        loc = Location(id=loc_id, business_id=biz_id, name="Silver Sands Main Property")
        session.add(loc)
        await session.flush()
        loc_id_str = str(loc_id)
    else:
        loc_id_str = location_id

    building = PropertyBuilding(location_id=loc_id_str, code="B1", name="Building 1", sort_order=0)
    session.add(building)
    await session.flush()

    floor_1 = PropertyFloor(building_id=building.id, floor_number=1, label="Floor 1", sort_order=0)
    session.add(floor_1)
    await session.flush()

    north = PropertySector(floor_id=floor_1.id, code="north", name="North Side", description="Rooms 7-12 on the north side", sort_order=0)
    south = PropertySector(floor_id=floor_1.id, code="south", name="South Side", description="Rooms 1-6 on the south side", sort_order=1)
    session.add_all([north, south])
    await session.flush()

    north_group = HKRoomGroup(location_id=loc_id_str, name="North Group", color="#3b82f6", description="North side rooms 7-12")
    south_group = HKRoomGroup(location_id=loc_id_str, name="South Group", color="#10b981", description="South side rooms 1-6")
    session.add_all([north_group, south_group])
    await session.flush()

    created_rooms = []
    for room_number in ["7", "8", "9", "10", "11", "12"]:
        room = HKRoom(
            location_id=loc_id_str, building_id=building.id, floor_id=floor_1.id,
            sector_id=north.id, room_group_id=north_group.id,
            room_number=room_number, room_label=f"Room {room_number}",
            room_type="standard", bed_count=2, bed_type_summary="2 queens",
            floor_surface=FloorSurface.carpet,
        )
        session.add(room)
        created_rooms.append(room)

    for room_number in ["1", "2", "3", "4", "5", "6"]:
        room = HKRoom(
            location_id=loc_id_str, building_id=building.id, floor_id=floor_1.id,
            sector_id=south.id, room_group_id=south_group.id,
            room_number=room_number, room_label=f"Room {room_number}",
            room_type="standard", bed_count=1, bed_type_summary="1 king",
            floor_surface=FloorSurface.carpet,
        )
        session.add(room)
        created_rooms.append(room)

    await session.flush()

    for room in created_rooms:
        for asset_data in STARTER_ASSETS:
            session.add(HKRoomAsset(room_id=room.id, **asset_data))
        for par_data in STARTER_SUPPLY_PARS:
            session.add(HKRoomSupplyPar(room_id=room.id, **par_data))

    await session.commit()
    log.info("Silver Sands seed complete: location_id=%s, rooms=%d", loc_id_str, len(created_rooms))

    return {
        "location_id": loc_id_str,
        "building_id": building.id,
        "floor_id": floor_1.id,
        "north_sector_id": north.id,
        "south_sector_id": south.id,
        "north_group_id": north_group.id,
        "south_group_id": south_group.id,
        "room_ids": [r.id for r in created_rooms],
    }


async def _main() -> None:
    from apps.api.app.core.config import get_settings
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        result = await seed_silver_sands(session)
        print("\nSeed result:")
        for k, v in result.items():
            print(f"  {k}: {v}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
