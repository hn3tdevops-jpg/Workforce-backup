"""
Idempotent utility to ensure a Business, Membership and Owner role/assignments exist for a user.
Provides a function that accepts a sync SQLAlchemy Session for use in tests and a CLI wrapper
that uses the repo's db_session() context manager.
"""
from __future__ import annotations

import uuid

from apps.api.app.db.base import import_models
from apps.api.app.core.db import db_session
from apps.api.app.models.user import User
from apps.api.app.models.tenant import Business
from apps.api.app.models.access_control import Membership, Role, ScopedRoleAssignment
from apps.api.app.services.rbac_seed_service import seed_default_roles_for_business


def ensure_business_membership(
    db,
    user_email: str,
    business_name: str = "Default Business",
    *,
    make_owner: bool = True,
) -> dict:
    """Ensure business exists and user is an active member with an Owner role.

    This function is idempotent and safe to run multiple times. It performs a two-phase
    operation where necessary to avoid FK flush ordering issues on SQLite:
      1. Ensure Business exists and Membership exists (commit/flush in caller's session).
      2. Ensure default roles & role_permissions exist for the business (uses seed_default_roles_for_business).
      3. Ensure a ScopedRoleAssignment links the membership -> Owner role.

    Returns a dict with keys: business_id, membership_id, owner_role_id, created (bool)
    """
    # Ensure models are loaded. import_models() may raise in test contexts where
    # the `app` package name is not present; fall back to importing the apps.api.app
    # model modules directly to be robust in different import layouts.
    try:
        import_models()
    except Exception:
        # Best-effort: import explicit modules by package path
        import importlib

        importlib.import_module("apps.api.app.models.tenant")
        importlib.import_module("apps.api.app.models.user")
        importlib.import_module("apps.api.app.models.access_control")

    # Lookup user
    user = db.query(User).filter(User.email == user_email).one_or_none()
    if user is None:
        raise ValueError(f"User with email {user_email} not found")

    # Ensure business
    biz = db.query(Business).filter(Business.name == business_name).one_or_none()
    created = False
    if not biz:
        biz = Business(id=uuid.uuid4(), name=business_name)
        db.add(biz)
        db.flush()
        created = True

    # Ensure membership
    membership = db.query(Membership).filter(
        Membership.user_id == user.id,
        Membership.business_id == biz.id,
    ).one_or_none()
    if not membership:
        membership = Membership(id=uuid.uuid4(), user_id=user.id, business_id=biz.id, status="active", is_owner=make_owner)
        db.add(membership)
        db.flush()
        created = True
    else:
        # reactivate if necessary
        if membership.status != "active":
            membership.status = "active"
            db.add(membership)
            db.flush()
            created = True

    # At this point, business + membership exist in this session. To avoid FK/flush ordering
    # issues when creating role_permissions, call seed_default_roles_for_business which is
    # implemented to be idempotent. It expects a SQLAlchemy Session and will flush as needed.
    roles = seed_default_roles_for_business(db, biz.id)

    owner_role = roles.get("Owner")
    if owner_role is None:
        # Fallback: try to query Role table directly
        owner_role = db.query(Role).filter(Role.business_id == biz.id, Role.name == "Owner").one_or_none()
        if owner_role is None:
            # Create minimal Owner role
            owner_role = Role(id=uuid.uuid4(), business_id=biz.id, name="Owner", description="Owner role", is_system=True)
            db.add(owner_role)
            db.flush()

    # Ensure scoped role assignment exists (business-wide -> location_id is NULL)
    sra = db.query(ScopedRoleAssignment).filter(ScopedRoleAssignment.membership_id == membership.id, ScopedRoleAssignment.role_id == owner_role.id).one_or_none()
    if not sra:
        sra = ScopedRoleAssignment(id=uuid.uuid4(), membership_id=membership.id, role_id=owner_role.id, location_id=None)
        db.add(sra)
        db.flush()
        created = True

    return {
        "business_id": str(biz.id),
        "membership_id": str(membership.id),
        "owner_role_id": str(owner_role.id),
        "created": created,
    }


def run_cli():
    """CLI wrapper used by ops to link an existing user to a business.

    Usage: python -m apps.api.app.cli.ensure_business_membership
    """
    import argparse

    parser = argparse.ArgumentParser(description="Ensure business + membership + owner role for a user")
    parser.add_argument("email")
    parser.add_argument("--business-name", default="Default Business")
    args = parser.parse_args()

    with db_session() as db:
        res = ensure_business_membership(db, args.email, business_name=args.business_name)
        print("Result:", res)


if __name__ == "__main__":
    run_cli()
