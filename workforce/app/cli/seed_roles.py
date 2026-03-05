"""
Seed RBAC roles and permissions as system templates.
Idempotent; safe to run multiple times.
"""
from typing import Dict, List

from sqlalchemy import select

from app.core.db import db_session
from app.services.audit import log_change
from app.models.identity import Permission, BizRole, BizRolePermission


def _get_or_create(db, model, **kwargs):
    row = db.execute(select(model).filter_by(**kwargs)).scalar_one_or_none()
    if row:
        return row, False
    obj = model(**kwargs)
    db.add(obj)
    db.flush()
    return obj, True


def run_seed_roles():
    """Create default permissions and system BizRole templates."""
    perm_keys = [
        "business:read",
        "business:manage",
        "members:read",
        "members:manage",
        "shifts:create",
        "shifts:assign",
        "shifts:manage",
        "timeclock:read",
        "timeclock:manage",
        "payroll:export",
        "messaging:read",
        "messaging:send",
        "marketplace:post",
        "training:manage",
        "locations:manage",
    ]

    role_templates: Dict[str, List[str]] = {
        "platform-admin": ["business:manage", "members:manage", "shifts:manage", "timeclock:manage", "payroll:export", "messaging:send", "messaging:read", "marketplace:post", "training:manage", "locations:manage"],
        "business-owner": ["business:manage", "members:manage", "shifts:manage", "timeclock:manage", "payroll:export", "messaging:read", "messaging:send", "marketplace:post", "training:manage", "locations:manage"],
        "manager": ["members:read", "shifts:create", "shifts:assign", "shifts:manage", "timeclock:read", "messaging:send", "messaging:read"],
        "staff": ["shifts:create", "timeclock:read", "messaging:read"],
        "location-manager": ["members:manage", "shifts:manage", "locations:manage", "messaging:read", "messaging:send"],
        "location-staff": ["shifts:create", "timeclock:read", "messaging:read"],
        "base-user": ["messaging:read"],
    }

    created_perms = 0
    created_roles = 0
    created_mappings = 0

    with db_session() as db:
        # Permissions
        perms = {}
        for key in perm_keys:
            p, created = _get_or_create(db, Permission, key=key)
            if created:
                log_change(db, "seed-rbac", None, "Permission", p.id, "create", None, {"key": key})
                created_perms += 1
            perms[key] = p

        # Roles (system templates)
        roles = {}
        for rname, pkeys in role_templates.items():
            r, created = _get_or_create(db, BizRole, business_id=None, name=rname, is_system_template=True)
            if created:
                log_change(db, "seed-rbac", None, "BizRole", r.id, "create", None, {"name": rname})
                created_roles += 1
            roles[rname] = r

            # Ensure mappings
            for key in pkeys:
                perm = perms.get(key)
                if not perm:
                    # Skip unknown permission keys
                    continue
                # check existing mapping
                existing = db.execute(
                    select(BizRolePermission).where(
                        BizRolePermission.role_id == r.id,
                        BizRolePermission.permission_id == perm.id,
                    )
                ).scalar_one_or_none()
                if not existing:
                    m = BizRolePermission(role_id=r.id, permission_id=perm.id)
                    db.add(m)
                    db.flush()
                    # composite id for audit
                    aud_id = f"{r.id}:{perm.id}"
                    log_change(db, "seed-rbac", None, "BizRolePermission", aud_id, "create", None, {"role_id": r.id, "permission_id": perm.id})
                    created_mappings += 1

    print("RBAC seed complete:")
    print(f"  Permissions created: {created_perms}")
    print(f"  Roles created      : {created_roles}")
    print(f"  Role mappings added: {created_mappings}")
