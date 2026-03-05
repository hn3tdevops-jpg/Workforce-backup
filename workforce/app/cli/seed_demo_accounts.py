"""
Demo account seeder.
Creates:
  - Business: Acme Coffee Co
  - Role: Owner  (all tenant permissions)
  - Role: Worker (schedule:read, schedule:write only)
  - User: demo-owner@workforce.app  → Owner role
  - User: demo-worker@workforce.app → Worker role
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.business import Business
from app.models.identity import (
    BizRole, BizRolePermission, Membership, MembershipRole,
    MembershipStatus, Permission, User, UserStatus,
)
from app.models.messaging import Channel, ChannelMember, ChannelType, MemberRole

OWNER_EMAIL    = "demo-owner@workforce.app"
OWNER_PASSWORD = "DemoOwner2026!"
WORKER_EMAIL   = "demo-worker@workforce.app"
WORKER_PASSWORD= "DemoWorker2026!"
BIZ_NAME       = "Acme Coffee Co"

OWNER_PERMS = [
    "members:read", "members:write",
    "roles:read", "roles:write",
    "locations:read", "locations:write", "owner:manage",
    "schedule:read", "schedule:write",
    "reports:read",
    "timeclock:read", "timeclock:write", "timeclock:manage",
    "marketplace:read", "marketplace:write", "marketplace:manage",
    "messaging:read", "messaging:write", "messaging:broadcast", "messaging:manage",
]
WORKER_PERMS = [
    "schedule:read",
    "timeclock:manage",
    "marketplace:read", "marketplace:write",
    "messaging:manage",
    "training:read",
]


def _upsert_user(db, email, password, is_superadmin=False):
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(email=email, hashed_password=hash_password(password),
                 is_superadmin=is_superadmin, status=UserStatus.active)
        db.add(u)
        db.flush()
        print(f"  Created user: {email}")
    else:
        u.status = UserStatus.active
        print(f"  Found existing user: {email}")
    return u


def _upsert_perm(db, key):
    p = db.query(Permission).filter(Permission.key == key).first()
    if not p:
        p = Permission(key=key)
        db.add(p)
        db.flush()
    return p


def _upsert_role(db, biz_id, name):
    r = db.query(BizRole).filter(BizRole.business_id == biz_id, BizRole.name == name).first()
    if not r:
        r = BizRole(business_id=biz_id, name=name)
        db.add(r)
        db.flush()
        print(f"  Created role: {name}")
    return r


def _assign_perms_to_role(db, role, perm_keys):
    """Sync role permissions — add missing, remove extras."""
    target_keys = set(perm_keys)
    # Upsert all target perms
    target_perm_ids = set()
    for key in target_keys:
        p = _upsert_perm(db, key)
        target_perm_ids.add(p.id)

    existing = db.query(BizRolePermission).filter(BizRolePermission.role_id == role.id).all()
    existing_by_perm = {brp.permission_id: brp for brp in existing}

    # Add missing
    for pid in target_perm_ids:
        if pid not in existing_by_perm:
            db.add(BizRolePermission(role_id=role.id, permission_id=pid))

    # Remove extras
    for pid, brp in existing_by_perm.items():
        if pid not in target_perm_ids:
            db.delete(brp)


def _upsert_membership(db, user, biz_id, role):
    m = db.query(Membership).filter(
        Membership.user_id == user.id,
        Membership.business_id == biz_id,
    ).first()
    if not m:
        m = Membership(user_id=user.id, business_id=biz_id, status=MembershipStatus.active)
        db.add(m)
        db.flush()
        print(f"  Created membership: {user.email} → {biz_id}")
    else:
        m.status = MembershipStatus.active

    mr = db.query(MembershipRole).filter(
        MembershipRole.membership_id == m.id,
        MembershipRole.role_id == role.id,
    ).first()
    if not mr:
        db.add(MembershipRole(membership_id=m.id, role_id=role.id))
    return m


def run_demo_seed():
    db = SessionLocal()
    try:
        print("\n── Demo Business ─────────────────────────────")
        biz = db.query(Business).filter(Business.name == BIZ_NAME).first()
        if not biz:
            biz = Business(name=BIZ_NAME, plan="pro")
            db.add(biz)
            db.flush()
            print(f"  Created business: {BIZ_NAME} ({biz.id})")
        else:
            print(f"  Found business: {BIZ_NAME} ({biz.id})")

        print("\n── Roles & Permissions ───────────────────────")
        owner_role  = _upsert_role(db, biz.id, "Owner")
        worker_role = _upsert_role(db, biz.id, "Worker")
        _assign_perms_to_role(db, owner_role,  OWNER_PERMS)
        _assign_perms_to_role(db, worker_role, WORKER_PERMS)
        print(f"  Owner  perms: {OWNER_PERMS}")
        print(f"  Worker perms: {WORKER_PERMS}")

        print("\n── Users & Memberships ───────────────────────")
        owner_user  = _upsert_user(db, OWNER_EMAIL,  OWNER_PASSWORD)
        worker_user = _upsert_user(db, WORKER_EMAIL, WORKER_PASSWORD)
        _upsert_membership(db, owner_user,  biz.id, owner_role)
        _upsert_membership(db, worker_user, biz.id, worker_role)

        db.commit()
        print("\n── Messaging Channels ────────────────────────")
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        for ch_name, ch_type in [("Announcements", ChannelType.announcement), ("General", ChannelType.group)]:
            existing_ch = db.query(Channel).filter(
                Channel.business_id == biz.id, Channel.name == ch_name
            ).first()
            if not existing_ch:
                ch = Channel(business_id=biz.id, name=ch_name, type=ch_type, created_by=owner_user.id)
                db.add(ch)
                db.flush()
                db.add(ChannelMember(channel_id=ch.id, user_id=owner_user.id, role=MemberRole.admin, joined_at=now))
                db.add(ChannelMember(channel_id=ch.id, user_id=worker_user.id, role=MemberRole.member, joined_at=now))
                print(f"  Created channel: {ch_name} ({ch_type})")
            else:
                print(f"  Found channel: {ch_name}")

        db.commit()
        print("\n── Done ──────────────────────────────────────")
        print(f"  Business:  {BIZ_NAME}  ({biz.id})")
        print(f"  Owner:     {OWNER_EMAIL}  /  {OWNER_PASSWORD}")
        print(f"  Worker:    {WORKER_EMAIL}  /  {WORKER_PASSWORD}")
        return {
            "business_id": biz.id,
            "business_name": BIZ_NAME,
            "owner_email": OWNER_EMAIL,
            "owner_password": OWNER_PASSWORD,
            "worker_email": WORKER_EMAIL,
            "worker_password": WORKER_PASSWORD,
        }
    finally:
        db.close()


if __name__ == "__main__":
    run_demo_seed()
