"""
Matching service tests using an in-memory SQLite database.
"""
import os
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Point at an in-memory DB before importing anything that touches settings
os.environ.setdefault("DATABASE_URL", "sqlite://")

from apps.api.app.models.base import Base
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
from apps.api.app.services.matching import find_candidates_for_shift


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    yield session
    session.rollback()
    session.close()


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


SHIFT_START = _dt("2026-03-01T09:00:00")
SHIFT_END   = _dt("2026-03-01T17:00:00")


def _make_scenario(db):
    """Create a reusable scenario and return key objects."""
    from apps.api.app.models.employee import Role

    biz = Business(name="Test Biz")
    db.add(biz)
    db.flush()

    loc = Location(business_id=biz.id, name="HQ", timezone="UTC")
    db.add(loc)
    db.flush()

    role = Role(name=f"cashier-{biz.id[:8]}")
    db.add(role)
    db.flush()

    other_role = Role(name=f"cook-{biz.id[:8]}")
    db.add(other_role)
    db.flush()

    shift = Shift(
        business_id=biz.id,
        location_id=loc.id,
        role_id=role.id,
        start_ts=SHIFT_START,
        end_ts=SHIFT_END,
        needed_count=1,
        status=ShiftStatus.published,
    )
    db.add(shift)
    db.flush()

    def make_employee(first, last, email, avail_status, proficiency,
                      role_override=None, emp_status=EmploymentStatus.active):
        e = Employee(first_name=first, last_name=last, email=email)
        db.add(e)
        db.flush()

        empl = Employment(business_id=biz.id, employee_id=e.id, status=emp_status)
        db.add(empl)
        db.flush()

        used_role = role_override or role
        er = EmployeeRole(employment_id=empl.id, role_id=used_role.id, proficiency=proficiency)
        db.add(er)
        db.flush()

        if avail_status is not None:
            ab = AvailabilityBlock(
                employee_id=e.id,
                start_ts=_dt("2026-03-01T08:00:00"),
                end_ts=_dt("2026-03-01T18:00:00"),
                status=avail_status,
            )
            db.add(ab)
            db.flush()

        return e, empl

    return biz, loc, role, other_role, shift, make_employee


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_preferred_comes_first(db):
    biz, loc, role, other_role, shift, make_emp = _make_scenario(db)

    emp_available, _ = make_emp("Zara", "Zee", f"zara{biz.id[:4]}@x.com",
                                AvailabilityStatus.available, 5)
    emp_preferred, _ = make_emp("Anna", "Aaa", f"anna{biz.id[:4]}@x.com",
                                AvailabilityStatus.preferred, 3)

    results = find_candidates_for_shift(db, shift.id)
    ids = [r["employee_id"] for r in results]

    assert emp_preferred.id in ids
    assert emp_available.id in ids
    # preferred must come before available
    assert ids.index(emp_preferred.id) < ids.index(emp_available.id)


def test_overlapping_assigned_excluded(db):
    biz, loc, role, other_role, shift, make_emp = _make_scenario(db)

    emp_ok, _ = make_emp("Bob", "Ok", f"bob{biz.id[:4]}@x.com",
                         AvailabilityStatus.preferred, 4)
    emp_busy, _ = make_emp("Carol", "Busy", f"carol{biz.id[:4]}@x.com",
                           AvailabilityStatus.preferred, 4)

    # Give busy employee an overlapping assignment
    other_shift = Shift(
        business_id=biz.id,
        location_id=loc.id,
        role_id=role.id,
        start_ts=_dt("2026-03-01T10:00:00"),
        end_ts=_dt("2026-03-01T15:00:00"),
        needed_count=1,
        status=ShiftStatus.published,
    )
    db.add(other_shift)
    db.flush()

    sa = ShiftAssignment(
        shift_id=other_shift.id,
        employee_id=emp_busy.id,
        status=AssignmentStatus.assigned,
    )
    db.add(sa)
    db.flush()

    results = find_candidates_for_shift(db, shift.id)
    ids = [r["employee_id"] for r in results]

    assert emp_ok.id in ids
    assert emp_busy.id not in ids


def test_inactive_employment_excluded(db):
    biz, loc, role, other_role, shift, make_emp = _make_scenario(db)

    emp_active, _   = make_emp("Dave", "Active",   f"dave{biz.id[:4]}@x.com",
                               AvailabilityStatus.available, 3)
    emp_inactive, _ = make_emp("Eve",  "Inactive", f"eve{biz.id[:4]}@x.com",
                               AvailabilityStatus.available, 3,
                               emp_status=EmploymentStatus.inactive)

    results = find_candidates_for_shift(db, shift.id)
    ids = [r["employee_id"] for r in results]

    assert emp_active.id in ids
    assert emp_inactive.id not in ids


def test_wrong_role_excluded(db):
    biz, loc, role, other_role, shift, make_emp = _make_scenario(db)

    emp_right_role, _ = make_emp("Frank", "Right", f"frank{biz.id[:4]}@x.com",
                                 AvailabilityStatus.available, 4)
    emp_wrong_role, _ = make_emp("Grace", "Wrong", f"grace{biz.id[:4]}@x.com",
                                 AvailabilityStatus.available, 4,
                                 role_override=other_role)

    results = find_candidates_for_shift(db, shift.id)
    ids = [r["employee_id"] for r in results]

    assert emp_right_role.id in ids
    assert emp_wrong_role.id not in ids


def test_shift_not_found(db):
    with pytest.raises(ValueError, match="not found"):
        find_candidates_for_shift(db, "00000000-0000-0000-0000-000000000000")
