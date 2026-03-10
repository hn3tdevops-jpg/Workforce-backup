# WORKFORCE RBAC — KEY CODE SNIPPETS

## 1. CORE RBAC MODELS (identity.py)

### Permission Model
```python
class Permission(UUIDMixin, Base):
    __tablename__ = "permissions"
    
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    # e.g., "schedule:read", "members:write", "roles:write"
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

### BizRole Model (Location-Scoped ✅)
```python
class BizRole(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "biz_roles"
    
    business_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True
    )  # NULL = system template
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_system_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # MASTER PLAN FIELDS ✅
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False, default="BUSINESS")
    # When scope_type='LOCATION', optionally pin to a specific location
    location_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    # Higher priority = preferred display role when a user holds multiple roles
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    permissions: Mapped[list["BizRolePermission"]] = relationship("BizRolePermission", back_populates="role")
    membership_roles: Mapped[list["MembershipRole"]] = relationship("MembershipRole", back_populates="role")
    
    __table_args__ = (
        UniqueConstraint("business_id", "name", name="uq_bizrole_business_name"),
    )
```

### MembershipLocationRole Model (Per-Location Assignments ✅)
```python
class MembershipLocationRole(Base):
    """Per-location role override — grants a member extra (or different) roles at a specific location."""
    __tablename__ = "membership_location_roles"
    
    membership_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memberships.id", ondelete="CASCADE"), primary_key=True
    )
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True
    )  # LOCATION SCOPE ✅
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("biz_roles.id", ondelete="CASCADE"), primary_key=True
    )
    
    # Display label for profile/job title; falls back to role.name if not set
    job_title_label: Mapped[str | None] = mapped_column(String(100), nullable=True)  # MASTER PLAN ✅
    created_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )  # MASTER PLAN ✅
    
    membership: Mapped["Membership"] = relationship("Membership", back_populates="location_roles")
    location: Mapped["Location"] = relationship("Location")
    role: Mapped["BizRole"] = relationship("BizRole")
```

---

## 2. RBAC ENFORCEMENT (auth_deps.py)

### Get User Permissions (Business-wide)
```python
def _get_user_permissions(user: User, business_id: str, db: Session) -> set[str]:
    """Return the set of permission keys the user holds in a business.
    Effective permissions = business-level role perms ∪ all location-level role perms.
    """
    if user.is_superadmin:
        return {"*"}  # superadmins have all permissions
    
    # Business-level permissions (via MembershipRole)
    biz_perms = db.execute(
        select(Permission.key)
        .join(BizRolePermission, BizRolePermission.permission_id == Permission.id)
        .join(BizRole, BizRole.id == BizRolePermission.role_id)
        .join(MembershipRole, MembershipRole.role_id == BizRole.id)
        .join(Membership, Membership.id == MembershipRole.membership_id)
        .where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalars().all()
    
    # Location-level permissions (via MembershipLocationRole — additive)
    loc_perms = db.execute(
        select(Permission.key)
        .join(BizRolePermission, BizRolePermission.permission_id == Permission.id)
        .join(BizRole, BizRole.id == BizRolePermission.role_id)
        .join(MembershipLocationRole, MembershipLocationRole.role_id == BizRole.id)
        .join(Membership, Membership.id == MembershipLocationRole.membership_id)
        .where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalars().all()
    
    return set(biz_perms) | set(loc_perms)  # Union
```

### Get User Permissions at Specific Location
```python
def _get_user_location_permissions(user: User, business_id: str, location_id: str, db: Session) -> set[str]:
    """Permissions at a specific location: business-wide role perms + location-scoped role perms for that location only."""
    if user.is_superadmin:
        return {"*"}
    
    biz_perms = db.execute(
        select(Permission.key)
        .join(BizRolePermission, BizRolePermission.permission_id == Permission.id)
        .join(BizRole, BizRole.id == BizRolePermission.role_id)
        .join(MembershipRole, MembershipRole.role_id == BizRole.id)
        .join(Membership, Membership.id == MembershipRole.membership_id)
        .where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalars().all()
    
    # Only permissions from roles at THIS location
    loc_perms = db.execute(
        select(Permission.key)
        .join(BizRolePermission, BizRolePermission.permission_id == Permission.id)
        .join(BizRole, BizRole.id == BizRolePermission.role_id)
        .join(MembershipLocationRole, MembershipLocationRole.role_id == BizRole.id)
        .join(Membership, Membership.id == MembershipLocationRole.membership_id)
        .where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
            MembershipLocationRole.location_id == location_id,  # ← THIS LOCATION ONLY
        )
    ).scalars().all()
    
    return set(biz_perms) | set(loc_perms)
```

### Permission Dependency
```python
def require_permission(permission_key: str):
    """
    Dependency factory. Usage:

        @router.get("/foo")
        def foo(
            user: CurrentUser,
            _: None = Depends(require_permission("schedule:read")),
            business_id: str = Path(...),
            location_id: str | None = Path(None),  # optional location scope
            db: Session = Depends(get_db),
        ):
    
    Behavior: if a location_id path parameter is present and not None, the
    dependency will validate the permission in the context of that location
    (business-wide permissions still apply). Otherwise it validates business-wide perms.
    """
    def _dep(
        user: CurrentUser,
        business_id: str,
        db: DBDep,
        location_id: str | None = None,
    ) -> None:
        # Ensure the user is a member of the business (superadmins bypass)
        _resolve_business_id(user, business_id, db)
        
        # If a location_id is supplied, check location-scoped permissions first
        if location_id:
            perms = _get_user_location_permissions(user, business_id, location_id, db)
        else:
            perms = _get_user_permissions(user, business_id, db)
        
        if "*" not in perms and permission_key not in perms:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"Missing permission: {permission_key}",
            )
    
    return Depends(_dep)
```

---

## 3. JOB TITLE DISPLAY (tenant/routes.py)

```python
def _derive_job_title(membership: "Membership", db: Session) -> str | None:
    """Compute a display job title for a membership from role assignments.
    
    Priority order:
    1. Location-scoped assignment at primary_location_id (highest role.priority first)
       - use job_title_label if set else role.name
    2. Business-level assignment (highest role.priority first)
       - use job_title_label if set else role.name
    Returns None if no assignments exist.
    """
    # Check location-scoped assignments first
    if membership.primary_location_id:
        loc_assignments = db.execute(
            select(MembershipLocationRole, BizRole)
            .join(BizRole, BizRole.id == MembershipLocationRole.role_id)
            .where(
                MembershipLocationRole.membership_id == membership.id,
                MembershipLocationRole.location_id == membership.primary_location_id,
            )
            .order_by(BizRole.priority.desc().nulls_last())  # Highest priority first ✅
        ).all()
        if loc_assignments:
            mlr, role = loc_assignments[0]
            # Use custom label if set, else role name ✅
            return mlr.job_title_label or role.name
    
    # Fallback to business-level assignments
    biz_assignments = db.execute(
        select(MembershipRole, BizRole)
        .join(BizRole, BizRole.id == MembershipRole.role_id)
        .where(MembershipRole.membership_id == membership.id)
        .order_by(BizRole.priority.desc().nulls_last())  # Highest priority first ✅
    ).all()
    if biz_assignments:
        mr, role = biz_assignments[0]
        # Use custom label if set, else role name ✅
        return mr.job_title_label or role.name
    
    return None
```

---

## 4. LOCATION ROLE ASSIGNMENT ENDPOINT (tenant/routes.py)

```python
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
    
    ⚠️ NOTE: Uses generic "roles:write" — should be location-specific permission
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
                created_by_user_id=user.id if user else None,  # Track who made the change ✅
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
```

---

## 5. DEFAULT PERMISSIONS & ROLES (roles_seed.py)

```python
DEFAULT_PERMISSIONS: list[dict] = [
    {"key": "schedule:read",       "description": "View schedules and shifts"},
    {"key": "schedule:write",      "description": "Create and edit schedules and shifts"},
    {"key": "members:read",        "description": "View team members"},
    {"key": "members:write",       "description": "Invite and manage team members"},
    {"key": "roles:read",          "description": "View roles and permissions"},
    {"key": "roles:write",         "description": "Create and edit roles"},
    {"key": "locations:read",      "description": "View locations"},
    {"key": "locations:write",     "description": "Edit locations"},
    {"key": "owner:manage",        "description": "Create locations and perform owner-level operations"},
    {"key": "timeclock:manage",    "description": "Clock in/out and manage all timeclock entries"},
    # ... more permissions
]

DEFAULT_ROLES: list[dict] = [
    {
        "name": "Manager",
        "priority": 80,  # ✅ Higher priority = preferred display
        "permissions": [
            "schedule:read", "schedule:write",
            "members:read", "members:write",
            "roles:read",
            "locations:read", "locations:write",
            # ... full permissions
        ],
    },
    {
        "name": "Supervisor",
        "priority": 70,
        "permissions": [
            "schedule:read", "schedule:write",
            "members:read",
            "timeclock:manage",
            # ... limited permissions
        ],
    },
    # ... more roles
]

def seed_permissions_and_roles(db: Session) -> dict:
    """Idempotently seed default permissions and system-template roles."""
    # 1. Ensure all permissions exist
    for pdata in DEFAULT_PERMISSIONS:
        existing = db.execute(
            select(Permission).where(Permission.key == pdata["key"])
        ).scalar_one_or_none()
        if not existing:
            p = Permission(key=pdata["key"], description=pdata["description"])
            db.add(p)
            db.flush()
    
    # 2. Ensure default roles exist with correct permissions
    for rdata in DEFAULT_ROLES:
        role = db.execute(
            select(BizRole).where(
                BizRole.name == rdata["name"],
                BizRole.is_system_template == True,
                BizRole.business_id == None,
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
        
        # Sync permissions
        for pkey in rdata["permissions"]:
            perm = db.execute(
                select(Permission).where(Permission.key == pkey)
            ).scalar_one_or_none()
            if perm and not db.execute(
                select(BizRolePermission).where(
                    BizRolePermission.role_id == role.id,
                    BizRolePermission.permission_id == perm.id,
                )
            ).scalar_one_or_none():
                db.add(BizRolePermission(role_id=role.id, permission_id=perm.id))
    
    db.commit()
    return {
        "permissions_created": perms_created,
        "permissions_total": len(DEFAULT_PERMISSIONS),
        "roles_created": roles_created,
        "roles_total": len(DEFAULT_ROLES),
    }
```

---

## 6. MIGRATIONS (Key Changes)

### Migration: Add scope_type, location_id, priority (b7c2e4f1a9d3)
```python
def upgrade() -> None:
    # ── biz_roles: scope_type, location_id, priority ─────────────────────────
    with op.batch_alter_table('biz_roles') as batch_op:
        batch_op.add_column(sa.Column('scope_type', sa.String(20), nullable=False, server_default='BUSINESS'))
        batch_op.add_column(sa.Column('location_id', sa.String(36), nullable=True))
        batch_op.add_column(sa.Column('priority', sa.Integer(), nullable=True))
    
    # ── membership_location_roles: job_title_label, created_by_user_id ───────
    with op.batch_alter_table('membership_location_roles') as batch_op:
        batch_op.add_column(sa.Column('job_title_label', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('created_by_user_id', sa.String(36), nullable=True))
    
    # ── membership_roles: job_title_label, created_by_user_id ────────────────
    with op.batch_alter_table('membership_roles') as batch_op:
        batch_op.add_column(sa.Column('job_title_label', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('created_by_user_id', sa.String(36), nullable=True))
```

---

## SUMMARY

✅ **Implemented**:
- Per-location RBAC with scope_type and location_id on roles
- Job title display with priority-based selection
- RBAC enforcement at route level via require_permission()
- Location-scoped role assignments via MembershipLocationRole
- Permission tracking with created_by_user_id

❌ **Missing**:
- Location owner delegation (rbac.location_roles.manage, rbac.location_assignments.manage)
- Audit logging for RBAC changes
- Effective permissions API endpoint
- Guard to prevent removing last location owner

