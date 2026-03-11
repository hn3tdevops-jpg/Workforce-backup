"""
Default permissions and roles seed data.
Run once on first startup or via POST /api/v1/control/roles/seed
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.models.identity import BizRole, BizRolePermission, Permission

# ── Canonical permission registry ──────────────────────────────────────────

DEFAULT_PERMISSIONS: list[dict] = [
    # Scheduling
    {"key": "schedule:read",       "description": "View schedules and shifts"},
    {"key": "schedule:write",      "description": "Create and edit schedules and shifts"},
    # Members / Team
    {"key": "members:read",        "description": "View team members"},
    {"key": "members:write",       "description": "Invite and manage team members"},
    # Roles
    {"key": "roles:read",          "description": "View roles and permissions"},
    {"key": "roles:write",         "description": "Create and edit roles"},
    # Locations
    {"key": "locations:read",      "description": "View locations"},
    {"key": "locations:write",     "description": "Edit locations"},
    {"key": "owner:manage",        "description": "Create locations and perform owner-level operations"},
    # Timeclock
    {"key": "timeclock:manage",    "description": "Clock in/out and manage all timeclock entries"},
    # Marketplace
    {"key": "marketplace:read",    "description": "Browse marketplace shift listings"},
    {"key": "marketplace:write",   "description": "Post and manage marketplace listings"},
    {"key": "marketplace:manage",  "description": "Manage job postings, swap requests, and coverage"},
    # Messaging
    {"key": "messaging:read",      "description": "View messaging channels and messages"},
    {"key": "messaging:write",     "description": "Send messages and create channels"},
    {"key": "messaging:broadcast", "description": "Post to announcement channels and broadcast"},
    {"key": "messaging:manage",    "description": "Manage channels, members, and API keys"},
    # Reports
    {"key": "report:read",         "description": "View reports and analytics"},
    # Training
    {"key": "training:read",       "description": "View training materials"},
    {"key": "training:write",      "description": "Create and edit training materials"},
]

# ── Default system-template roles ──────────────────────────────────────────

DEFAULT_ROLES: list[dict] = [
    {
        "name": "Manager",
        "priority": 80,
        "permissions": [
            "schedule:read", "schedule:write",
            "members:read", "members:write",
            "roles:read",
            "locations:read", "locations:write",
            "timeclock:manage",
            "marketplace:read", "marketplace:write", "marketplace:manage",
            "messaging:read", "messaging:write", "messaging:broadcast", "messaging:manage",
            "report:read",
            "training:read", "training:write",
        ],
    },
    {
        "name": "Supervisor",
        "priority": 70,
        "permissions": [
            "schedule:read", "schedule:write",
            "members:read",
            "timeclock:manage",
            "marketplace:read", "marketplace:manage",
            "messaging:read", "messaging:write", "messaging:broadcast", "messaging:manage",
            "report:read",
            "training:read",
        ],
    },
    {
        "name": "Employee",
        "priority": 50,
        "permissions": [
            "schedule:read",
            "timeclock:manage",
            "marketplace:read", "marketplace:write",
            "messaging:read", "messaging:write", "messaging:manage",
            "training:read",
        ],
    },
    {
        "name": "Viewer",
        "priority": 10,
        "permissions": [
            "schedule:read",
            "report:read",
        ],
    },
]


def seed_permissions_and_roles(db: Session) -> dict:
    """Idempotently seed default permissions and system-template roles.

    Returns a summary dict with counts of created/skipped items.
    """
    perms_created = 0
    roles_created = 0

    # 1. Ensure all permissions exist
    perm_map: dict[str, Permission] = {}
    for pdata in DEFAULT_PERMISSIONS:
        existing = db.execute(
            select(Permission).where(Permission.key == pdata["key"])
        ).scalar_one_or_none()
        if existing:
            perm_map[pdata["key"]] = existing
        else:
            p = Permission(key=pdata["key"], description=pdata["description"])
            db.add(p)
            db.flush()
            perm_map[pdata["key"]] = p
            perms_created += 1

    # 2. Ensure default roles exist with correct permissions
    for rdata in DEFAULT_ROLES:
        role = db.execute(
            select(BizRole).where(
                BizRole.name == rdata["name"],
                BizRole.is_system_template == True,  # noqa: E712
                BizRole.business_id == None,  # noqa: E711
            )
        ).scalar_one_or_none()

        if not role:
            role = BizRole(
                name=rdata["name"],
                is_system_template=True,
                business_id=None,
                scope_type=rdata.get("scope_type", "BUSINESS"),
                priority=rdata.get("priority"),
            )
            db.add(role)
            db.flush()
            roles_created += 1
        else:
            # Sync priority and scope_type in case they changed
            role.priority = rdata.get("priority")
            role.scope_type = rdata.get("scope_type", "BUSINESS")

        # Sync permissions — add missing ones (don't remove extras)
        existing_perm_ids = {
            brp.permission_id
            for brp in db.execute(
                select(BizRolePermission).where(BizRolePermission.role_id == role.id)
            ).scalars().all()
        }
        for pkey in rdata["permissions"]:
            perm = perm_map.get(pkey)
            if perm and perm.id not in existing_perm_ids:
                db.add(BizRolePermission(role_id=role.id, permission_id=perm.id))

    db.commit()
    return {
        "permissions_created": perms_created,
        "permissions_total": len(DEFAULT_PERMISSIONS),
        "roles_created": roles_created,
        "roles_total": len(DEFAULT_ROLES),
    }


def provision_business_defaults(business_id: str, db: Session) -> dict:
    """Copy all system-template roles into a business as business-specific roles.

    Idempotent — skips roles whose name already exists in the business.
    Call this whenever a new business is created.
    """
    templates = db.execute(
        select(BizRole).where(
            BizRole.is_system_template == True,  # noqa: E712
            BizRole.business_id == None,          # noqa: E711
        )
    ).scalars().all()

    roles_created = 0
    for tmpl in templates:
        existing = db.execute(
            select(BizRole).where(BizRole.business_id == business_id, BizRole.name == tmpl.name)
        ).scalar_one_or_none()
        if existing:
            continue

        role = BizRole(
            business_id=business_id,
            name=tmpl.name,
            is_system_template=False,
            scope_type=tmpl.scope_type,
            priority=tmpl.priority,
        )
        db.add(role)
        db.flush()

        # Copy all permission assignments from the template
        tmpl_perms = db.execute(
            select(BizRolePermission).where(BizRolePermission.role_id == tmpl.id)
        ).scalars().all()
        for tp in tmpl_perms:
            db.add(BizRolePermission(role_id=role.id, permission_id=tp.permission_id))

        roles_created += 1

    db.commit()
    return {"business_id": business_id, "roles_provisioned": roles_created}
