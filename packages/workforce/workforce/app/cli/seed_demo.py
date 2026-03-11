"""
Demo seed: creates one business, three employees, a shift, and validates matching.
All writes produce audit_log rows.
"""
from datetime import datetime, timezone

from apps.api.app.core.db import db_session
from apps.api.app.models.business import Business, Location
from apps.api.app.models.employee import Employee, EmployeeRole, Employment, EmploymentStatus
from apps.api.app.models.scheduling import (
    AssignmentStatus,
    AvailabilityBlock,
    AvailabilityStatus,
    Shift,
    ShiftAssignment,
    ShiftStatus,
)
from apps.api.app.services.audit import log_change


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def _get_or_create(db, model, **kwargs):
    """Fetch existing row or create a new one."""
    from sqlalchemy import select
    row = db.execute(select(model).filter_by(**kwargs)).scalar_one_or_none()
    if row:
        return row, False
    obj = model(**kwargs)
    db.add(obj)
    db.flush()
    return obj, True


def _seed_into(db) -> dict:
    """Core seed logic; idempotent — safe to call multiple times."""
    from apps.api.app.models.employee import Role  # noqa

    # --- Business + Location (always fresh per seed run) ---
    biz = Business(name="Acme Diner")
    db.add(biz)
    db.flush()
    log_change(db, "seed", None, "Business", biz.id, "create", None, {"name": biz.name})

    loc = Location(business_id=biz.id, name="Main Street Branch", timezone="America/New_York")
    db.add(loc)
    db.flush()
    log_change(db, "seed", None, "Location", loc.id, "create", None, {"name": loc.name})

    # --- Roles (shared/global — get or create) ---
    roles = {}
    for rname in ["cashier", "cook", "server"]:
        r, created = _get_or_create(db, Role, name=rname)
        if created:
            log_change(db, "seed", None, "Role", r.id, "create", None, {"name": rname})
        roles[rname] = r

    # --- Core permissions (idempotent) ---
    perm_keys = [
        "timeclock:read",
        "timeclock:manage",
        "shifts:create",
        "shifts:assign",
        "members:read",
        "hk:manage",
        "payroll:export",
    ]
    perms = {}
    from apps.api.app.models.identity import Permission
    for key in perm_keys:
        p, created = _get_or_create(db, Permission, key=key)
        if created:
            log_change(db, "seed", None, "Permission", p.id, "create", None, {"key": key})
        perms[key] = p

    # --- Employees (unique emails per seed run via biz id suffix) ---
    suffix = biz.id[:8]
    emp_data = [
        ("Alice", "Andersen", f"alice-{suffix}@example.com"),
        ("Bob",   "Brown",    f"bob-{suffix}@example.com"),
        ("Carol", "Clark",    f"carol-{suffix}@example.com"),
    ]
    employees = []
    employments = []
    for first, last, email in emp_data:
        e = Employee(first_name=first, last_name=last, email=email)
        db.add(e)
        db.flush()
        log_change(db, "seed", None, "Employee", e.id, "create", None,
                   {"first_name": first, "last_name": last, "email": email})

        empl = Employment(business_id=biz.id, employee_id=e.id, status=EmploymentStatus.active)
        db.add(empl)
        db.flush()
        log_change(db, "seed", None, "Employment", empl.id, "create", None,
                   {"business_id": biz.id, "employee_id": e.id})

        employees.append(e)
        employments.append(empl)

    alice, bob, carol = employees
    alice_empl, bob_empl, carol_empl = employments

    # Proficiencies: Alice=5 (preferred), Bob=3 (available), Carol=4 (unavailable)
    for empl, proficiency in [(alice_empl, 5), (bob_empl, 3), (carol_empl, 4)]:
        er = EmployeeRole(
            employment_id=empl.id, role_id=roles["cashier"].id, proficiency=proficiency
        )
        db.add(er)
        db.flush()
        log_change(db, "seed", None, "EmployeeRole", er.id, "create", None,
                   {"employment_id": empl.id, "role_id": roles["cashier"].id,
                    "proficiency": proficiency})

    # --- Shift: 2026-02-20 09:00-17:00 UTC ---
    shift_start = _dt("2026-02-20T09:00:00")
    shift_end   = _dt("2026-02-20T17:00:00")

    shift = Shift(
        business_id=biz.id,
        location_id=loc.id,
        role_id=roles["cashier"].id,
        start_ts=shift_start,
        end_ts=shift_end,
        needed_count=2,
        status=ShiftStatus.published,
    )
    db.add(shift)
    db.flush()
    log_change(db, "seed", None, "Shift", shift.id, "create", None,
               {"start_ts": str(shift_start), "end_ts": str(shift_end)})

    # --- Availability blocks ---
    ab_alice = AvailabilityBlock(
        employee_id=alice.id,
        start_ts=_dt("2026-02-20T08:00:00"),
        end_ts=_dt("2026-02-20T18:00:00"),
        status=AvailabilityStatus.preferred,
    )
    db.add(ab_alice)
    db.flush()
    log_change(db, "seed", None, "AvailabilityBlock", ab_alice.id, "create", None,
               {"employee_id": alice.id, "status": "preferred"})

    ab_bob = AvailabilityBlock(
        employee_id=bob.id,
        start_ts=_dt("2026-02-20T08:00:00"),
        end_ts=_dt("2026-02-20T18:00:00"),
        status=AvailabilityStatus.available,
    )
    db.add(ab_bob)
    db.flush()
    log_change(db, "seed", None, "AvailabilityBlock", ab_bob.id, "create", None,
               {"employee_id": bob.id, "status": "available"})

    ab_carol = AvailabilityBlock(
        employee_id=carol.id,
        start_ts=_dt("2026-02-20T08:00:00"),
        end_ts=_dt("2026-02-20T18:00:00"),
        status=AvailabilityStatus.unavailable,
    )
    db.add(ab_carol)
    db.flush()
    log_change(db, "seed", None, "AvailabilityBlock", ab_carol.id, "create", None,
               {"employee_id": carol.id, "status": "unavailable"})

    # --- Overlapping assignment for Bob ---
    other_shift = Shift(
        business_id=biz.id,
        location_id=loc.id,
        role_id=roles["cashier"].id,
        start_ts=_dt("2026-02-20T10:00:00"),
        end_ts=_dt("2026-02-20T14:00:00"),
        needed_count=1,
        status=ShiftStatus.published,
    )
    db.add(other_shift)
    db.flush()
    log_change(db, "seed", None, "Shift", other_shift.id, "create", None,
               {"note": "overlap shift for Bob"})

    bob_assignment = ShiftAssignment(
        shift_id=other_shift.id,
        employee_id=bob.id,
        status=AssignmentStatus.assigned,
    )
    db.add(bob_assignment)
    db.flush()
    log_change(db, "seed", None, "ShiftAssignment", bob_assignment.id, "create", None,
               {"shift_id": other_shift.id, "employee_id": bob.id, "status": "assigned"})

    return {
        "business_name": biz.name,
        "business_id": biz.id,
        "location_id": loc.id,
        "shift_id": shift.id,
        "shift_start": str(shift_start),
        "shift_end": str(shift_end),
    }


def run_seed():
    """CLI entry point — wraps _seed_into in a managed session."""
    with db_session() as db:
        result = _seed_into(db)

    print("=" * 60)
    print(f"Business  : {result['business_name']} ({result['business_id']})")
    print(f"Shift ID  : {result['shift_id']}  [{result['shift_start']} - {result['shift_end']}]")
    print("=" * 60)
    print("\nRun matching with:")
    print(f"  python -m app.cli.main match --shift-id {result['shift_id']}")


def run_seed_return(db) -> dict:
    """API entry point — uses caller's session, returns key IDs."""
    return _seed_into(db)
