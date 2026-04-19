"""
HKops demo seed — populates sample rooms, task types, and tasks for testing.
Uses the first business found in the DB (run seed-demo first).
"""
from datetime import datetime, timezone

from sqlalchemy import select

from apps.api.app.core.db import db_session
from apps.api.app.models.business import Business, Location
from apps.api.app.models.hkops import (
    HKRoom, HKTaskType, HKTask,
    RoomStatus, TaskPriority, TaskStatus,
)
from apps.api.app.models.identity import User


def _now() -> datetime:
    return datetime.now(timezone.utc)


ROOM_DATA = [
    # (room_number, floor, wing, room_type, status)
    ("101", "1", "East", "Standard Double",  RoomStatus.dirty),
    ("102", "1", "East", "Standard Double",  RoomStatus.clean),
    ("103", "1", "East", "King Suite",        RoomStatus.inspected),
    ("104", "1", "West", "Standard Single",   RoomStatus.dirty),
    ("201", "2", "East", "Deluxe King",       RoomStatus.dirty),
    ("202", "2", "East", "Deluxe King",       RoomStatus.do_not_disturb),
    ("203", "2", "West", "Standard Double",   RoomStatus.out_of_order),
    ("204", "2", "West", "Standard Double",   RoomStatus.clean),
    ("301", "3", "East", "Penthouse Suite",   RoomStatus.dirty),
    ("302", "3", "East", "Standard Single",   RoomStatus.clean),
]

TASK_TYPE_DATA = [
    # (name, duration_minutes, requires_inspection)
    ("Checkout Clean",   45, True),
    ("Stay-Over Clean",  25, False),
    ("Deep Clean",       90, True),
    ("Touch-Up",         10, False),
    ("Inspection",       15, False),
    ("Turn-Down Service", 20, False),
]


def run_hk_seed():
    with db_session() as db:
        # Find existing business
        biz = db.execute(select(Business).limit(1)).scalar_one_or_none()
        if not biz:
            print("❌  No business found — run `seed-demo` first.")
            return

        loc = db.execute(
            select(Location).where(Location.business_id == biz.id).limit(1)
        ).scalar_one_or_none()

        # Find a user to act as creator
        creator = db.execute(select(User).limit(1)).scalar_one_or_none()
        if not creator:
            print("❌  No user found — run `seed-demo-accounts` first.")
            return

        print(f"🏨  Seeding HKops for: {biz.name} ({biz.id})")

        # ── Task Types ──────────────────────────────────────────────────────
        task_types = {}
        for name, dur, req_insp in TASK_TYPE_DATA:
            existing = db.execute(
                select(HKTaskType).where(
                    HKTaskType.business_id == biz.id,
                    HKTaskType.name == name,
                )
            ).scalar_one_or_none()
            if not existing:
                tt = HKTaskType(
                    business_id=biz.id,
                    name=name,
                    default_duration_minutes=dur,
                    requires_inspection=req_insp,
                )
                db.add(tt)
                db.flush()
                task_types[name] = tt
                print(f"  ✚ task type: {name}")
            else:
                task_types[name] = existing

        # ── Rooms ───────────────────────────────────────────────────────────
        rooms = {}
        for room_number, floor, wing, room_type, status in ROOM_DATA:
            existing = db.execute(
                select(HKRoom).where(
                    HKRoom.business_id == biz.id,
                    HKRoom.room_number == room_number,
                )
            ).scalar_one_or_none()
            if not existing:
                room = HKRoom(
                    business_id=biz.id,
                    location_id=loc.id if loc else None,
                    room_number=room_number,
                    floor=floor,
                    wing=wing,
                    room_type=room_type,
                    status=status,
                )
                db.add(room)
                db.flush()
                rooms[room_number] = room
                print(f"  ✚ room: {room_number} ({room_type}) — {status.value}")
            else:
                rooms[room_number] = existing

        # ── Tasks (assign dirty rooms to checkout/stay-over cleans) ─────────
        today = _now().date().isoformat()
        dirty_rooms = [r for num, r in rooms.items() if r.status == RoomStatus.dirty]
        checkout_tt = task_types["Checkout Clean"]
        stayover_tt = task_types["Stay-Over Clean"]

        assignments = [
            (dirty_rooms[0], checkout_tt, TaskPriority.urgent, "08:00", "08:45"),
            (dirty_rooms[1], stayover_tt, TaskPriority.high,   "09:00", "09:25"),
            (dirty_rooms[2], checkout_tt, TaskPriority.normal, "10:00", "10:45"),
        ]

        for room, tt, priority, start, end in assignments:
            existing = db.execute(
                select(HKTask).where(
                    HKTask.room_id == room.id,
                    HKTask.scheduled_date == today,
                    HKTask.task_type_id == tt.id,
                )
            ).scalar_one_or_none()
            if not existing:
                task = HKTask(
                    business_id=biz.id,
                    room_id=room.id,
                    task_type_id=tt.id,
                    created_by=creator.id,
                    priority=priority,
                    scheduled_date=today,
                    scheduled_start=start,
                    scheduled_end=end,
                    status=TaskStatus.pending,
                )
                db.add(task)
                db.flush()
                print(f"  ✚ task: room {room.room_number} → {tt.name} @ {start} [{priority.value}]")

        print("\n✅  HKops seed complete.")
        print(f"   Business ID : {biz.id}")
        print(f"   Rooms seeded: {len(rooms)}")
        print(f"   Task types  : {len(task_types)}")
