from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from apps.api.app.models.employee import Employee, EmployeeRole, Employment, EmploymentStatus
from apps.api.app.models.scheduling import (
    AssignmentStatus,
    AvailabilityBlock,
    AvailabilityStatus,
    Shift,
    ShiftAssignment,
)

# Statuses that constitute a blocking assignment (employee already committed elsewhere)
BLOCKING_STATUSES = {
    AssignmentStatus.offered,
    AssignmentStatus.assigned,
    AssignmentStatus.checked_in,
}


def find_candidates_for_shift(session: Session, shift_id: str) -> list[dict[str, Any]]:
    """
    Return eligible candidates for a shift, sorted by:
      1. preferred availability before available
      2. proficiency DESC
      3. last_name ASC

    Tenant safety: candidates must have active Employment in shift.business_id.
    """
    shift = session.get(Shift, shift_id)
    if shift is None:
        raise ValueError(f"Shift {shift_id!r} not found")

    # Subquery: employee has a blocking overlapping assignment on another shift
    overlapping_assignment = (
        select(ShiftAssignment.employee_id)
        .join(Shift, Shift.id == ShiftAssignment.shift_id)
        .where(
            ShiftAssignment.status.in_(list(BLOCKING_STATUSES)),
            ShiftAssignment.shift_id != shift_id,
            Shift.start_ts < shift.end_ts,
            Shift.end_ts > shift.start_ts,
        )
    )

    stmt = (
        select(
            Employee,
            AvailabilityBlock.status.label("avail_status"),
            EmployeeRole.proficiency,
        )
        .join(Employment, Employment.employee_id == Employee.id)
        .join(EmployeeRole, EmployeeRole.employment_id == Employment.id)
        .join(
            AvailabilityBlock,
            and_(
                AvailabilityBlock.employee_id == Employee.id,
                AvailabilityBlock.start_ts <= shift.start_ts,
                AvailabilityBlock.end_ts >= shift.end_ts,
                AvailabilityBlock.status.in_(
                    [AvailabilityStatus.preferred, AvailabilityStatus.available]
                ),
            ),
        )
        .where(
            Employment.business_id == shift.business_id,
            Employment.status == EmploymentStatus.active,
            EmployeeRole.role_id == shift.role_id,
            Employee.id.not_in(overlapping_assignment),
        )
    )

    rows = session.execute(stmt).all()

    # Sort: preferred first (0), then available (1), then proficiency DESC, last_name ASC
    def sort_key(row):
        avail_order = 0 if row.avail_status == AvailabilityStatus.preferred else 1
        return (avail_order, -row.proficiency, row.Employee.last_name)

    rows = sorted(rows, key=sort_key)

    results = []
    seen: set[str] = set()
    for row in rows:
        emp = row.Employee
        if emp.id in seen:
            continue
        seen.add(emp.id)
        results.append(
            {
                "employee_id": emp.id,
                "first_name": emp.first_name,
                "last_name": emp.last_name,
                "email": emp.email,
                "proficiency": row.proficiency,
                "availability_status": row.avail_status,
            }
        )
    return results
