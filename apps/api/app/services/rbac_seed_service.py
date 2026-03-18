from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.access_control import Permission, Role, RolePermission


DEFAULT_ROLE_PERMISSION_CODES: dict[str, set[str]] = {
    "Owner": {
        "users.read",
        "users.manage",
        "businesses.read",
        "businesses.manage",
        "locations.read",
        "locations.manage",
        "schedule.read",
        "schedule.manage",
        "time.read",
        "time.manage",
        "inventory.read",
        "inventory.manage",
        "hk.rooms.read",
        "hk.tasks.manage",
    },
    "Admin": {
        "users.read",
        "users.manage",
        "businesses.read",
        "locations.read",
        "locations.manage",
        "schedule.read",
        "schedule.manage",
        "time.read",
        "time.manage",
        "inventory.read",
        "inventory.manage",
        "hk.rooms.read",
        "hk.tasks.manage",
    },
    "Manager": {
        "users.read",
        "locations.read",
        "schedule.read",
        "schedule.manage",
        "time.read",
        "inventory.read",
        "hk.rooms.read",
        "hk.tasks.manage",
    },
    "Supervisor": {
        "locations.read",
        "schedule.read",
        "time.read",
        "hk.rooms.read",
        "hk.tasks.manage",
    },
    "Staff": {
        "schedule.read",
        "time.read",
        "hk.rooms.read",
    },
}


def _permission_parts(code: str) -> tuple[str, str]:
    resource, action = code.rsplit(".", 1)
    return resource, action


def ensure_permissions_exist(session: Session, codes: set[str]) -> dict[str, Permission]:
    existing = {
        perm.code: perm
        for perm in session.scalars(
            select(Permission).where(Permission.code.in_(sorted(codes)))
        ).all()
    }

    missing = codes - set(existing.keys())
    for code in sorted(missing):
        resource, action = _permission_parts(code)
        perm = Permission(
            id=uuid.uuid4(),
            code=code,
            resource=resource,
            action=action,
            description=code,
        )
        session.add(perm)
        existing[code] = perm

    session.flush()
    return existing


def seed_default_roles_for_business(session: Session, business_id: uuid.UUID | str) -> dict[str, Role]:
    all_codes = set().union(*DEFAULT_ROLE_PERMISSION_CODES.values())
    permissions_by_code = ensure_permissions_exist(session, all_codes)

    existing_roles = {
        role.name: role
        for role in session.scalars(
            select(Role).where(Role.business_id == business_id)
        ).all()
    }

    for role_name in DEFAULT_ROLE_PERMISSION_CODES:
        if role_name not in existing_roles:
            role = Role(
                id=uuid.uuid4(),
                business_id=business_id,
                name=role_name,
                description=f"Default {role_name} role",
                is_system=True,
            )
            session.add(role)
            existing_roles[role_name] = role

    session.flush()

    existing_pairs = set(
        session.execute(
            select(RolePermission.role_id, RolePermission.permission_id).join(
                Role, Role.id == RolePermission.role_id
            ).where(Role.business_id == business_id)
        ).all()
    )

    for role_name, permission_codes in DEFAULT_ROLE_PERMISSION_CODES.items():
        role = existing_roles[role_name]
        for code in sorted(permission_codes):
            permission = permissions_by_code[code]
            pair = (role.id, permission.id)
            if pair not in existing_pairs:
                session.add(RolePermission(role_id=role.id, permission_id=permission.id))
                existing_pairs.add(pair)

    session.flush()
    return existing_roles