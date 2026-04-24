from __future__ import annotations

import uuid
from sqlalchemy import distinct, or_, select
from typing import Any

from app.models.access_control import Membership, Permission, Role, RolePermission, ScopedRoleAssignment


async def get_effective_role_names_async(
    session: Any,
    user_id: uuid.UUID | str,
    business_id: uuid.UUID | str,
    location_id: uuid.UUID | str | None = None,
) -> set[str]:
    stmt = (
        select(distinct(Role.name))
        .select_from(Membership)
        .join(ScopedRoleAssignment, ScopedRoleAssignment.membership_id == Membership.id)
        .join(Role, Role.id == ScopedRoleAssignment.role_id)
        .where(Membership.user_id == user_id)
        .where(Membership.business_id == business_id)
        .where(Membership.status == "active")
        .where(Role.business_id == business_id)
    )

    if location_id is None:
        stmt = stmt.where(ScopedRoleAssignment.location_id.is_(None))
    else:
        stmt = stmt.where(
            or_(
                ScopedRoleAssignment.location_id.is_(None),
                ScopedRoleAssignment.location_id == location_id,
            )
        )

    rows = await session.scalars(stmt)
    return set(rows.all())


async def get_effective_permission_codes_async(
    session: Any,
    user_id: uuid.UUID | str,
    business_id: uuid.UUID | str,
    location_id: uuid.UUID | str | None = None,
) -> set[str]:
    stmt = (
        select(distinct(Permission.code))
        .select_from(Membership)
        .join(ScopedRoleAssignment, ScopedRoleAssignment.membership_id == Membership.id)
        .join(Role, Role.id == ScopedRoleAssignment.role_id)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(Membership.user_id == user_id)
        .where(Membership.business_id == business_id)
        .where(Membership.status == "active")
        .where(Role.business_id == business_id)
    )

    if location_id is None:
        stmt = stmt.where(ScopedRoleAssignment.location_id.is_(None))
    else:
        stmt = stmt.where(
            or_(
                ScopedRoleAssignment.location_id.is_(None),
                ScopedRoleAssignment.location_id == location_id,
            )
        )

    rows = await session.scalars(stmt)
    return set(rows.all())


async def user_has_permission_async(
    session: Any,
    user_id: uuid.UUID | str,
    permission_code: str,
    business_id: uuid.UUID | str,
    location_id: uuid.UUID | str | None = None,
) -> bool:
    perms = await get_effective_permission_codes_async(
        session=session, user_id=user_id, business_id=business_id, location_id=location_id
    )
    return permission_code in perms
