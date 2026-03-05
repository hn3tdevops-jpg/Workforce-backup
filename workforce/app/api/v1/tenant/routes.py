"""
Tenant plane routes — business owners / managers.
All routes scoped to a business_id path parameter.
Requires an active membership + relevant RBAC permission.
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.auth_deps import (
    CurrentUser, require_membership, require_permission,
)
from app.core.db import get_db
from app.models.business import Location
from app.models.identity import (
    BizRole, BizRolePermission, Membership, MembershipLocationRole, MembershipRole,
    MembershipStatus, Permission, User, UserStatus, WorkerProfile,
)

router = APIRouter(prefix="/api/v1/tenant/{business_id}", tags=["tenant"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _derive_job_title(membership: "Membership", db: Session) -> str | None:
    """Compute a display job title for a membership from role assignments.

    Priority order:
    1. Location-scoped assignment at primary_location_id (highest role.priority first)
       - use job_title_label if set, else role.name
    2. Business-level assignment (highest role.priority first)
       - use job_title_label if set, else role.name
    Returns None if no assignments exist.
    """
    if membership.primary_location_id:
        loc_assignments = db.execute(
            select(MembershipLocationRole, BizRole)
            .join(BizRole, BizRole.id == MembershipLocationRole.role_id)
            .where(
                MembershipLocationRole.membership_id == membership.id,
                MembershipLocationRole.location_id == membership.primary_location_id,
            )
            .order_by(BizRole.priority.desc().nulls_last())
        ).all()
        if loc_assignments:
            mlr, role = loc_assignments[0]
            return mlr.job_title_label or role.name

    biz_assignments = db.execute(
        select(MembershipRole, BizRole)
        .join(BizRole, BizRole.id == MembershipRole.role_id)
        .where(MembershipRole.membership_id == membership.id)
        .order_by(BizRole.priority.desc().nulls_last())
    ).all()
    if biz_assignments:
        mr, role = biz_assignments[0]
        return mr.job_title_label or role.name

    return None


# ── Memberships ───────────────────────────────────────────────────────────────

@router.get("/members", dependencies=[require_permission("members:read")])
def list_members(
    business_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
    q: str | None = None,           # search email
    status: str | None = None,      # active | invited | inactive | removed
    role_id: str | None = None,     # filter by role
    location_id: str | None = None, # filter by primary location
):
    stmt = select(Membership).where(Membership.business_id == business_id)
    if status:
        try:
            stmt = stmt.where(Membership.status == MembershipStatus(status))
        except ValueError:
            pass
    else:
        stmt = stmt.where(Membership.status != MembershipStatus.removed)

    memberships = db.execute(stmt).scalars().all()

    if location_id:
        memberships = [m for m in memberships if m.primary_location_id == location_id]

    # Filter by role
    if role_id:
        role_member_ids = {
            mr.membership_id
            for mr in db.execute(
                select(MembershipRole).where(MembershipRole.role_id == role_id)
            ).scalars().all()
        }
        memberships = [m for m in memberships if m.id in role_member_ids]

    # Resolve user emails and filter by search term
    user_ids = [m.user_id for m in memberships]
    users_by_id: dict[str, User] = {}
    if user_ids:
        for u in db.execute(select(User).where(User.id.in_(user_ids))).scalars().all():
            users_by_id[u.id] = u

    if q:
        q_lower = q.lower()
        memberships = [
            m for m in memberships
            if q_lower in users_by_id.get(m.user_id, User(email="")).email.lower()
        ]

    # Load all roles for this business for display (include system templates for legacy assignments)
    all_roles_by_id: dict[str, BizRole] = {
        r.id: r
        for r in db.execute(
            select(BizRole).where(
                (BizRole.business_id == business_id) | (BizRole.is_system_template.is_(True))
            )
        ).scalars().all()
    }

    # Load role assignments for these memberships
    membership_ids = [m.id for m in memberships]
    roles_by_membership: dict[str, list[str]] = {}
    if membership_ids:
        for mr in db.execute(
            select(MembershipRole).where(MembershipRole.membership_id.in_(membership_ids))
        ).scalars().all():
            role = all_roles_by_id.get(mr.role_id)
            if role:
                roles_by_membership.setdefault(mr.membership_id, []).append(role.name)

    # Load worker profiles
    from app.models.identity import WorkerProfile
    profiles_by_membership: dict[str, WorkerProfile] = {}
    if membership_ids:
        for wp in db.execute(
            select(WorkerProfile).where(WorkerProfile.membership_id.in_(membership_ids))
        ).scalars().all():
            profiles_by_membership[wp.membership_id] = wp

    result = []
    for m in memberships:
        u = users_by_id.get(m.user_id)
        wp = profiles_by_membership.get(m.id)
        job_title = _derive_job_title(m, db) or (wp.job_title if wp else None)
        result.append({
            "id": m.id,
            "user_id": m.user_id,
            "email": u.email if u else m.user_id,
            "first_name": u.first_name if u else None,
            "last_name": u.last_name if u else None,
            "phone": u.phone if u else None,
            "user_status": u.status if u else None,
            "status": m.status,
            "primary_location_id": m.primary_location_id,
            "roles": roles_by_membership.get(m.id, []),
            "job_title": job_title,
            "pay_rate": wp.pay_rate if wp else None,
        })

    return sorted(result, key=lambda x: x["email"])


class InviteRequest(BaseModel):
    email: str
    role_ids: list[str] = []


@router.post("/members", status_code=201, dependencies=[require_permission("members:write")])
def invite_member(
    business_id: str,
    payload: InviteRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    target = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not target:
        # Auto-create a stub user
        target = User(email=payload.email, hashed_password="", status=UserStatus.invited)
        db.add(target)
        db.flush()

    existing = db.execute(
        select(Membership).where(
            Membership.user_id == target.id,
            Membership.business_id == business_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "User already has a membership in this business")

    membership = Membership(
        user_id=target.id,
        business_id=business_id,
        status=MembershipStatus.invited,
    )
    db.add(membership)
    db.flush()

    for role_id in payload.role_ids:
        db.add(MembershipRole(membership_id=membership.id, role_id=role_id))

    db.commit()
    return {"membership_id": membership.id, "user_id": target.id, "email": target.email}


@router.patch("/members/{membership_id}/status", dependencies=[require_permission("members:write")])
def update_member_status(
    business_id: str,
    membership_id: str,
    new_status: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    m = db.get(Membership, membership_id)
    if not m or m.business_id != business_id:
        raise HTTPException(404, "Membership not found")
    try:
        m.status = MembershipStatus(new_status)
    except ValueError:
        raise HTTPException(400, f"Invalid status: {new_status}")
    db.commit()
    return {"membership_id": m.id, "status": m.status}


class MemberProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    bio: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    job_title: str | None = None
    pay_rate: float | None = None
    hire_date: str | None = None
    notes: str | None = None
    primary_location_id: str | None = None
    status: str | None = None


@router.get("/members/{membership_id}/profile", dependencies=[require_permission("members:read")])
def get_member_profile(
    business_id: str,
    membership_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    m = db.get(Membership, membership_id)
    if not m or m.business_id != business_id:
        raise HTTPException(404, "Membership not found")
    u = db.get(User, m.user_id)
    wp = db.execute(select(WorkerProfile).where(WorkerProfile.membership_id == m.id)).scalar_one_or_none()
    roles = db.execute(
        select(BizRole).join(MembershipRole, BizRole.id == MembershipRole.role_id)
        .where(MembershipRole.membership_id == m.id)
    ).scalars().all()

    # Derive job_title from role assignments (location-scoped first, then business-level)
    job_title = _derive_job_title(m, db)
    if job_title is None and wp:
        job_title = wp.job_title  # legacy fallback

    return {
        "membership_id": m.id,
        "user_id": u.id,
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "phone": u.phone,
        "bio": u.bio,
        "emergency_contact_name": u.emergency_contact_name,
        "emergency_contact_phone": u.emergency_contact_phone,
        "status": m.status,
        "primary_location_id": m.primary_location_id,
        "roles": [{"id": r.id, "name": r.name} for r in roles],
        "job_title": job_title,
        "pay_rate": wp.pay_rate if wp else None,
        "hire_date": wp.hire_date if wp else None,
        "notes": wp.notes if wp else None,
        "member_since": str(m.created_at) if m.created_at else None,
    }


@router.patch("/members/{membership_id}/profile", dependencies=[require_permission("members:write")])
def update_member_profile(
    business_id: str,
    membership_id: str,
    payload: MemberProfileUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    m = db.get(Membership, membership_id)
    if not m or m.business_id != business_id:
        raise HTTPException(404, "Membership not found")
    u = db.get(User, m.user_id)
    updates = payload.model_dump(exclude_none=True)
    user_fields = {"first_name", "last_name", "phone", "bio", "emergency_contact_name", "emergency_contact_phone"}
    wp_fields = {"job_title", "pay_rate", "hire_date", "notes"}
    for field, value in updates.items():
        if field in user_fields:
            setattr(u, field, value)
    if "primary_location_id" in updates:
        m.primary_location_id = updates["primary_location_id"]
    if "status" in updates:
        try:
            m.status = MembershipStatus(updates["status"])
        except ValueError:
            raise HTTPException(400, f"Invalid status: {updates['status']}")
    wp_updates = {k: v for k, v in updates.items() if k in wp_fields}
    if wp_updates:
        wp = db.execute(select(WorkerProfile).where(WorkerProfile.membership_id == m.id)).scalar_one_or_none()
        if not wp:
            wp = WorkerProfile(membership_id=m.id)
            db.add(wp)
        for field, value in wp_updates.items():
            setattr(wp, field, value)
    db.commit()
    return get_member_profile(business_id, membership_id, db, user)


class MemberRolesUpdate(BaseModel):
    role_ids: list[str]


@router.put("/members/{membership_id}/roles", dependencies=[require_permission("members:write")])
def set_member_roles(
    business_id: str,
    membership_id: str,
    payload: MemberRolesUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    m = db.get(Membership, membership_id)
    if not m or m.business_id != business_id:
        raise HTTPException(404, "Membership not found")
    db.execute(delete(MembershipRole).where(MembershipRole.membership_id == membership_id))
    for role_id in payload.role_ids:
        role = db.get(BizRole, role_id)
        if role and role.business_id == business_id:
            db.add(MembershipRole(membership_id=membership_id, role_id=role_id))
    db.commit()
    return {"membership_id": membership_id, "role_ids": payload.role_ids}


@router.patch("/members/{membership_id}/remove", dependencies=[require_permission("members:write")])
def remove_member(
    business_id: str,
    membership_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    m = db.get(Membership, membership_id)
    if not m or m.business_id != business_id:
        raise HTTPException(404, "Membership not found")
    m.status = MembershipStatus.removed
    db.commit()
    return {"membership_id": membership_id, "status": "removed"}


# ── Roles ─────────────────────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    name: str
    is_system_template: bool = False


@router.get("/roles", dependencies=[require_permission("roles:read")])
def list_roles(business_id: str, db: Session = Depends(get_db), user: CurrentUser = None):
    rows = db.execute(select(BizRole).where(BizRole.business_id == business_id)).scalars().all()
    return [{"id": r.id, "name": r.name, "scope_type": r.scope_type, "priority": r.priority, "is_system_template": r.is_system_template} for r in rows]


@router.post("/roles/provision", dependencies=[require_permission("roles:write")])
def provision_roles(business_id: str, db: Session = Depends(get_db), user: CurrentUser = None):
    """Copy any missing system-template roles into this business. Idempotent."""
    from app.services.roles_seed import provision_business_defaults
    return provision_business_defaults(business_id, db)


@router.post("/roles", status_code=201, dependencies=[require_permission("roles:write")])
def create_role(
    business_id: str,
    payload: RoleCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    existing = db.execute(
        select(BizRole).where(BizRole.business_id == business_id, BizRole.name == payload.name)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Role name already exists in this business")
    role = BizRole(business_id=business_id, name=payload.name, is_system_template=payload.is_system_template)
    db.add(role)
    db.commit()
    db.refresh(role)
    return {"id": role.id, "name": role.name}


@router.post("/roles/{role_id}/permissions", dependencies=[require_permission("roles:write")])
def assign_permission_to_role(
    business_id: str,
    role_id: str,
    permission_key: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    role = db.get(BizRole, role_id)
    if not role or role.business_id != business_id:
        raise HTTPException(404, "Role not found")
    perm = db.execute(select(Permission).where(Permission.key == permission_key)).scalar_one_or_none()
    if not perm:
        perm = Permission(key=permission_key)
        db.add(perm)
        db.flush()
    existing = db.execute(
        select(BizRolePermission).where(
            BizRolePermission.role_id == role_id,
            BizRolePermission.permission_id == perm.id,
        )
    ).scalar_one_or_none()
    if not existing:
        db.add(BizRolePermission(role_id=role_id, permission_id=perm.id))
    db.commit()
    return {"role_id": role_id, "permission": permission_key}


# ── Business Settings ────────────────────────────────────────────────────────

# Valid swap_workflow values
SWAP_WORKFLOW_OPTIONS = ("auto_post", "manager_approval_first")


class BusinessSettingsUpdate(BaseModel):
    swap_workflow: str = "auto_post"  # "auto_post" | "manager_approval_first"


@router.get("/settings", dependencies=[require_permission("members:read")])
def get_business_settings(business_id: str, db: Session = Depends(get_db), user: CurrentUser = None):
    from app.models.business import Business
    biz = db.get(Business, business_id)
    if not biz:
        raise HTTPException(404, "Business not found")
    settings = json.loads(biz.settings_json or "{}") if biz.settings_json else {}
    settings.setdefault("swap_workflow", "auto_post")
    return settings


@router.patch("/settings", dependencies=[require_permission("members:write")])
def update_business_settings(
    business_id: str,
    payload: BusinessSettingsUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    from app.models.business import Business
    if payload.swap_workflow not in SWAP_WORKFLOW_OPTIONS:
        raise HTTPException(400, f"swap_workflow must be one of: {SWAP_WORKFLOW_OPTIONS}")
    biz = db.get(Business, business_id)
    if not biz:
        raise HTTPException(404, "Business not found")
    settings = json.loads(biz.settings_json or "{}") if biz.settings_json else {}
    settings["swap_workflow"] = payload.swap_workflow
    biz.settings_json = json.dumps(settings)
    db.commit()
    return settings


# ── Locations ─────────────────────────────────────────────────────────────────

class LocationCreate(BaseModel):
    name: str
    timezone: str = "UTC"
    settings: dict = {}
    parent_id: str | None = None


@router.get("/locations", dependencies=[require_membership()])
def list_locations(
    business_id: str,
    parent_id: str | None = None,
    include_all: bool = False,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    stmt = select(Location).where(Location.business_id == business_id)
    if include_all:
        pass  # return all locations regardless of depth
    elif parent_id is not None:
        stmt = stmt.where(Location.parent_id == parent_id)
    else:
        # Default: return only root locations (no parent)
        stmt = stmt.where(Location.parent_id.is_(None))
    rows = db.execute(stmt).scalars().all()
    # Build parent name lookup for display_name
    parent_ids = {loc.parent_id for loc in rows if loc.parent_id}
    parent_map: dict[str, str] = {}
    if parent_ids:
        parents = db.execute(
            select(Location).where(Location.id.in_(parent_ids))
        ).scalars().all()
        parent_map = {p.id: p.name for p in parents}
    return [
        {
            "id": loc.id,
            "name": loc.name,
            "display_name": f"{parent_map[loc.parent_id]} › {loc.name}" if loc.parent_id and loc.parent_id in parent_map else loc.name,
            "timezone": loc.timezone,
            "parent_id": loc.parent_id,
        }
        for loc in rows
    ]


@router.post("/locations", status_code=201, dependencies=[require_permission("owner:manage")])
def create_location(
    business_id: str,
    payload: LocationCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    if payload.parent_id:
        parent = db.execute(
            select(Location).where(
                Location.id == payload.parent_id, Location.business_id == business_id
            )
        ).scalar_one_or_none()
        if not parent:
            raise HTTPException(404, "Parent location not found in this business")
    loc = Location(
        business_id=business_id,
        name=payload.name,
        timezone=payload.timezone,
        settings_json=json.dumps(payload.settings),
        parent_id=payload.parent_id,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return {"id": loc.id, "name": loc.name, "timezone": loc.timezone, "parent_id": loc.parent_id}


@router.post(
    "/locations/{location_id}/sub-locations",
    status_code=201,
    dependencies=[require_permission("owner:manage")],
)
def create_sub_location(
    business_id: str,
    location_id: str,
    payload: LocationCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    parent = db.execute(
        select(Location).where(Location.id == location_id, Location.business_id == business_id)
    ).scalar_one_or_none()
    if not parent:
        raise HTTPException(404, "Location not found")
    loc = Location(
        business_id=business_id,
        name=payload.name,
        timezone=payload.timezone,
        settings_json=json.dumps(payload.settings),
        parent_id=location_id,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return {"id": loc.id, "name": loc.name, "timezone": loc.timezone, "parent_id": loc.parent_id}


@router.get(
    "/locations/{location_id}/sub-locations",
    dependencies=[require_permission("locations:read")],
)
def list_sub_locations(
    business_id: str,
    location_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    parent = db.execute(
        select(Location).where(Location.id == location_id, Location.business_id == business_id)
    ).scalar_one_or_none()
    if not parent:
        raise HTTPException(404, "Location not found")
    rows = db.execute(select(Location).where(Location.parent_id == location_id)).scalars().all()
    return [
        {
            "id": loc.id,
            "name": loc.name,
            "display_name": f"{parent.name} › {loc.name}",
            "timezone": loc.timezone,
            "parent_id": loc.parent_id,
        }
        for loc in rows
    ]


@router.delete("/locations/{location_id}", status_code=204, dependencies=[require_permission("owner:manage")])
def delete_location(
    business_id: str,
    location_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    loc = db.execute(
        select(Location).where(Location.id == location_id, Location.business_id == business_id)
    ).scalar_one_or_none()
    if not loc:
        raise HTTPException(404, "Location not found")
    db.execute(delete(Location).where(Location.id == location_id, Location.business_id == business_id))
    db.commit()


# ── Location-level Role Assignments ──────────────────────────────────────────

@router.get("/members/{membership_id}/location-roles", dependencies=[require_permission("roles:read")])
def get_member_location_roles(
    business_id: str,
    membership_id: str,
    db: Session = Depends(get_db),
):
    """Return per-location role assignments for a member, grouped by location_id."""
    m = db.get(Membership, membership_id)
    if not m or m.business_id != business_id:
        raise HTTPException(404, "Membership not found")
    rows = db.execute(
        select(MembershipLocationRole).where(MembershipLocationRole.membership_id == membership_id)
    ).scalars().all()
    # Group by location_id → list of role_ids
    result: dict[str, list[str]] = {}
    for r in rows:
        result.setdefault(r.location_id, []).append(r.role_id)
    return result


class LocationRolesPayload(BaseModel):
    # Dict of location_id → list of role_ids to assign (replaces all for that location)
    assignments: dict[str, list[str]]
    # Optional per-location, per-role job title labels: {location_id: {role_id: label}}
    job_title_labels: dict[str, dict[str, str]] = {}


@router.put("/members/{membership_id}/location-roles", dependencies=[require_permission("roles:write")])
def set_member_location_roles(
    business_id: str,
    membership_id: str,
    payload: LocationRolesPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    """Replace location-role assignments for a member. Only affects locations present in the payload.
    Requires roles:write permission.
    """
    m = db.get(Membership, membership_id)
    if not m or m.business_id != business_id:
        raise HTTPException(404, "Membership not found")

    for location_id, role_ids in payload.assignments.items():

        # Verify location belongs to this business
        loc = db.execute(
            select(Location).where(Location.id == location_id, Location.business_id == business_id)
        ).scalar_one_or_none()
        if not loc:
            raise HTTPException(404, f"Location {location_id} not found in this business")
        # Delete existing assignments for this location
        db.execute(
            delete(MembershipLocationRole).where(
                MembershipLocationRole.membership_id == membership_id,
                MembershipLocationRole.location_id == location_id,
            )
        )
        # Add new ones
        loc_labels = payload.job_title_labels.get(location_id, {})
        for role_id in role_ids:
            role = db.execute(
                select(BizRole).where(BizRole.id == role_id, BizRole.business_id == business_id)
            ).scalar_one_or_none()
            if not role:
                raise HTTPException(404, f"Role {role_id} not found in this business")
            db.add(MembershipLocationRole(
                membership_id=membership_id,
                location_id=location_id,
                role_id=role_id,
                job_title_label=loc_labels.get(role_id),
                created_by_user_id=user.id if user else None,
            ))
    db.commit()
    # Return updated state
    rows = db.execute(
        select(MembershipLocationRole).where(MembershipLocationRole.membership_id == membership_id)
    ).scalars().all()
    result: dict[str, list[str]] = {}
    for r in rows:
        result.setdefault(r.location_id, []).append(r.role_id)
    return result


# ── Directory Prospects ───────────────────────────────────────────────────────

@router.get("/directory/prospects", dependencies=[require_permission("members:read")])
def list_directory_prospects(
    business_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
    q: str | None = None,   # search by email/name
):
    """Return active users who are not current (active/invited) members of this business.
    These are candidate workers that can be invited or messaged from the Directory.
    """
    # Collect user_ids already in this business (active or invited — not removed/inactive which are treated as gone)
    existing_user_ids = {
        m.user_id
        for m in db.execute(
            select(Membership).where(
                Membership.business_id == business_id,
                Membership.status.in_([MembershipStatus.active, MembershipStatus.invited]),
            )
        ).scalars().all()
    }

    stmt = select(User).where(
        User.status == UserStatus.active,
        User.id.notin_(existing_user_ids) if existing_user_ids else True,
    )
    users = db.execute(stmt).scalars().all()

    if q:
        q_lower = q.lower()
        users = [
            u for u in users
            if q_lower in u.email.lower()
            or q_lower in (u.first_name or "").lower()
            or q_lower in (u.last_name or "").lower()
        ]

    # Load WorkerProfiles for these users via their memberships in any business
    # (we want the most recent WorkerProfile, or the one from any business they belong to)
    user_ids = [u.id for u in users]
    # Find any membership to get a worker profile
    any_memberships: dict[str, str] = {}  # user_id → membership_id
    if user_ids:
        for m in db.execute(
            select(Membership).where(Membership.user_id.in_(user_ids))
        ).scalars().all():
            any_memberships.setdefault(m.user_id, m.id)

    membership_ids = list(any_memberships.values())
    profiles_by_membership: dict[str, WorkerProfile] = {}
    if membership_ids:
        for wp in db.execute(
            select(WorkerProfile).where(WorkerProfile.membership_id.in_(membership_ids))
        ).scalars().all():
            profiles_by_membership[wp.membership_id] = wp

    def _jl(v):
        try:
            return json.loads(v) if v else []
        except Exception:
            return []

    result = []
    for u in users:
        mid = any_memberships.get(u.id)
        wp = profiles_by_membership.get(mid) if mid else None
        result.append({
            "user_id": u.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "phone": u.phone,
            "bio": u.bio,
            "job_title": wp.job_title if wp else None,
            "skills": _jl(wp.skills) if wp else [],
            "certifications": _jl(wp.certifications) if wp else [],
            "qualified_roles": _jl(wp.qualified_roles) if wp else [],
        })

    return sorted(result, key=lambda x: x["email"])


# ── Service-to-Service Integration endpoints ─────────────────────────────────
# These endpoints are intended for trusted internal services (e.g., housekeeping)
# that forward a valid JWT token from workforce.

@router.get("/integrations/staff", dependencies=[require_permission("members:read")])
def integration_list_eligible_staff(
    business_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
    location_id: str | None = None,
    role: str | None = None,
):
    """
    List active members optionally filtered by location and role name.
    Designed for service-to-service calls (housekeeping → workforce).
    """
    from app.models.identity import BizRole, MembershipRole
    stmt = (
        select(Membership, User)
        .join(User, User.id == Membership.user_id)
        .where(
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
            User.status == UserStatus.active,
        )
    )
    if location_id:
        stmt = stmt.where(Membership.primary_location_id == location_id)

    pairs = db.execute(stmt).all()

    if role:
        # Filter to members who have a BizRole matching the role name
        filtered = []
        for m, u in pairs:
            role_names = db.execute(
                select(BizRole.name)
                .join(MembershipRole, MembershipRole.role_id == BizRole.id)
                .where(MembershipRole.membership_id == m.id)
            ).scalars().all()
            if role.lower() in [r.lower() for r in role_names]:
                filtered.append((m, u))
        pairs = filtered

    return [
        {
            "user_id": u.id,
            "membership_id": m.id,
            "email": u.email,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "primary_location_id": m.primary_location_id,
        }
        for m, u in pairs
    ]


# ── Housekeeping integration: receive task events ─────────────────────────────

class HKEventPayload(BaseModel):
    event: str  # "task_assigned" | "task_completed"
    task_id: str
    employee_id: str | None = None
    room_id: str | None = None
    service_date: str | None = None
    completed_at: str | None = None


@router.post("/integrations/hk-events", status_code=202, dependencies=[require_permission("members:read")])
def receive_hk_event(
    business_id: str,
    payload: HKEventPayload,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Receive housekeeping task lifecycle events (task_assigned, task_completed).
    Writes an AuditEvent for traceability; returns 202 Accepted.
    Only callable by a JWT bearer that has the members:read permission (service-to-service).
    """
    from app.models.identity import AuditEvent
    from datetime import datetime as _dt, timezone as _tz
    audit = AuditEvent(
        business_id=business_id,
        actor_type="service",
        actor_id=user.id,
        action=f"hk.{payload.event}",
        entity="hk_task",
        entity_id=payload.task_id,
        diff_json=json.dumps({
            "event": payload.event,
            "employee_id": payload.employee_id,
            "room_id": payload.room_id,
            "service_date": payload.service_date,
            "completed_at": payload.completed_at,
        }),
        created_at=_dt.now(_tz.utc),
    )
    db.add(audit)
    db.commit()
    return {"accepted": True, "event": payload.event, "task_id": payload.task_id}
