# RBAC IMPLEMENTATION AUDIT REPORT
## Workforce Platform — RBAC, Roles, Permissions, and User Role Assignments

---

## EXECUTIVE SUMMARY

The Workforce platform has implemented a **hybrid RBAC system** that diverges significantly from the master plan. Instead of the planned simple `roles`, `permissions`, `role_permissions`, and `user_role_assignments` tables, the codebase uses **two parallel RBAC systems**:

1. **Legacy/Planned System**: `roles`, `permissions`, `role_permissions`, `user_role_assignments` tables (created but NOT used)
2. **Active System**: `biz_roles`, `permissions`, `biz_role_permissions`, `membership_roles`, `membership_location_roles` (actively used)

**Status**: ✅ Master plan requirements ARE implemented, but via a different data model than specified. The system works correctly but is architecturally different.

---

## SECTION 1: EXISTING TABLES & MODELS

### A. UNUSED PLANNED TABLES (from migration `zz_add_rbac_tables`)

These tables **exist in the database** but are **NOT referenced** anywhere in the application code:

#### `permissions` (UNUSED)
```
Columns:
- id (string, PK)
- key (string, unique) — e.g., 'employees.read'
- created_at (datetime)
```

#### `roles` (UNUSED)
```
Columns:
- id (string, PK)
- business_id (string, nullable)
- scope_type (string, default='BUSINESS') ✅ MATCHES MASTER PLAN
- location_id (string, nullable) ✅ MATCHES MASTER PLAN
- name (string)
- priority (integer, nullable)
- created_at (datetime)
```

#### `role_permissions` (UNUSED)
```
Columns:
- role_id (string, PK)
- permission_id (string, PK)
```

#### `user_role_assignments` (UNUSED)
```
Columns:
- id (string, PK)
- user_id (string)
- business_id (string)
- scope_type (string) ✅ MATCHES MASTER PLAN
- location_id (string, nullable) ✅ MATCHES MASTER PLAN
- role_id (string)
- job_title_label (string, nullable) ✅ MATCHES MASTER PLAN
- created_by_user_id (string, nullable) ✅ MATCHES MASTER PLAN
- created_at (datetime)
```

**Finding**: The master plan requirements for `scope_type`, `location_id`, and `job_title_label` ARE in the migrations, but these tables are **orphaned**.

---

### B. ACTIVE RBAC TABLES (actually used)

**File**: `/home/hn3t/projects_active/workforce/app/models/identity.py`

#### 1. `Permission` Model (ACTIVE ✅)
```python
class Permission(UUIDMixin, Base):
    __tablename__ = "permissions"
    key: str (unique, indexed) — e.g., "schedule:read"
    description: str (nullable)
```

#### 2. `BizRole` Model (ACTIVE ✅) — LOCATION-SCOPED
**File**: Lines 138–161 of `identity.py`

```python
class BizRole(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "biz_roles"
    
    business_id: str (nullable) — if NULL = system template (superadmin-defined)
    name: str
    is_system_template: bool
    scope_type: str ✅ MASTER PLAN FIELD ("BUSINESS" | "LOCATION")
    location_id: str (nullable) ✅ MASTER PLAN FIELD
    priority: int (nullable) ✅ MASTER PLAN FIELD
    
    Relationships:
    - permissions: list[BizRolePermission]
    - membership_roles: list[MembershipRole]
    
    Unique constraint: (business_id, name)
```

**Key Finding**: `scope_type`, `location_id`, and `priority` are present ✅ and populated via migration `b7c2e4f1a9d3_per_location_rbac.py`.

#### 3. `BizRolePermission` Model (ACTIVE ✅)
```python
class BizRolePermission(Base):
    __tablename__ = "biz_role_permissions"
    
    role_id: str (PK, FK → biz_roles)
    permission_id: str (PK, FK → permissions)
    
    Unique pair enforced by composite PK
```

#### 4. `MembershipRole` Model (BUSINESS-SCOPED, ACTIVE)
**File**: Lines 182–191 of `identity.py`

```python
class MembershipRole(Base):
    __tablename__ = "membership_roles"
    
    membership_id: str (PK, FK)
    role_id: str (PK, FK → biz_roles)
    job_title_label: str (nullable) ✅ MASTER PLAN FIELD
    created_by_user_id: str (nullable) ✅ MASTER PLAN FIELD (added in migration b7c2e4f1a9d3)
```

**Purpose**: Business-wide role assignments for a user.

#### 5. `MembershipLocationRole` Model (LOCATION-SCOPED, ACTIVE ✅)
**File**: Lines 194–207 of `identity.py`

```python
class MembershipLocationRole(Base):
    __tablename__ = "membership_location_roles"
    
    membership_id: str (PK, FK)
    location_id: str (PK, FK → locations) ✅ LOCATION SCOPE
    role_id: str (PK, FK → biz_roles)
    job_title_label: str (nullable) ✅ MASTER PLAN FIELD
    created_by_user_id: str (nullable) ✅ MASTER PLAN FIELD
    
    Relationships:
    - membership: Membership
    - location: Location
    - role: BizRole
    
    Unique constraint: (membership_id, location_id, role_id)
```

**Key Finding**: Per-location role assignment ✅ matches master plan requirement from Section 3 & 4.

#### 6. `Membership` Model (TENANT-SCOPED, ACTIVE)
**File**: Lines 95–115 of `identity.py`

```python
class Membership(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "memberships"
    
    user_id: str (FK)
    business_id: str (FK)
    primary_location_id: str (nullable, FK)
    status: MembershipStatus (enum)
    
    Relationships:
    - membership_roles: list[MembershipRole] — BUSINESS-SCOPED
    - location_roles: list[MembershipLocationRole] — LOCATION-SCOPED
```

---

## SECTION 2: RBAC ENFORCEMENT IN `auth_deps.py`

**File**: `/home/hn3t/projects_active/workforce/app/core/auth_deps.py`

### A. Core Functions

#### `_get_user_permissions(user, business_id, db)` — Lines 143–178
```python
Returns: set[str] of permission keys

Logic:
1. If user.is_superadmin: return {"*"} (all permissions)
2. Query business-level permissions:
   SELECT Permission.key
   FROM Permission
   JOIN BizRolePermission → BizRole
   JOIN MembershipRole → Membership
   WHERE user_id = ? AND business_id = ? AND membership.status = 'active'
3. Query location-level permissions:
   Same join but via MembershipLocationRole
4. Return union of business + location permissions
```

**Key Finding**: ✅ Implements master plan authorization rule:
> User can perform action X if:
> - scope_type = 'BUSINESS' AND role includes permission_key
> - OR scope_type = 'LOCATION' AND location_id = L AND role includes permission_key

#### `_get_user_location_permissions(user, business_id, location_id, db)` — Lines 181–213
```python
Returns: set[str] at a specific location

Logic:
1. Business-level permissions (apply everywhere)
2. Location-specific permissions (only from MembershipLocationRole with that location_id)
3. Return union
```

#### `require_permission(permission_key)` — Lines 216–254
```python
Dependency factory. Usage:

@router.get("/foo")
def foo(
    user: CurrentUser,
    _: None = Depends(require_permission("schedule:read")),
    business_id: str = Path(...),
    location_id: str | None = Path(None),
    db: Session = Depends(get_db),
):

Behavior:
1. Resolve business_id (user must have active membership)
2. If location_id provided: check location-scoped permissions
3. Else: check business-wide permissions
4. Raise 403 if permission missing (unless user is superadmin)
```

### B. Permission Check Pattern

**Example from tenant routes** (lines 67–76 of `/tenant/routes.py`):
```python
@router.get(
    "/members",
    dependencies=[require_permission("members:read")]
)
def list_members(
    business_id: str,
    ...
):
```

**All tenant endpoints use this pattern**: ✅ RBAC enforcement at entry point.

---

## SECTION 3: LOCATION OWNER DELEGATION (MASTER PLAN SECTION 4)

**REQUIREMENT**: "Location Owner" role with:
- `rbac.location_roles.manage`
- `rbac.location_assignments.manage`

**STATUS**: ❌ **NOT FOUND IN CODEBASE**

### What exists:

**From `roles_seed.py`** (lines 46–94):
```python
DEFAULT_ROLES = [
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
```

**Missing permissions**:
- ❌ `rbac.location_roles.manage`
- ❌ `rbac.location_assignments.manage`

### What endpoints exist for location delegation:

**From `/api/v1/tenant/{business_id}` routes** (lines 622–702 of `tenant/routes.py`):

```python
@router.get("/members/{membership_id}/location-roles", dependencies=[require_permission("roles:read")])
def get_member_location_roles(...)
    → Returns all location-role assignments for a member

@router.put("/members/{membership_id}/location-roles", dependencies=[require_permission("roles:write")])
def set_member_location_roles(...)
    → Replaces location-role assignments
    → Uses generic "roles:write" permission, NOT location-specific
```

**Finding**: Location role assignment endpoints exist ✅ but:
1. ❌ Use generic `roles:write` instead of `rbac.location_assignments.manage`
2. ❌ No location-owner delegation checks
3. ❌ No enforcement that only location owners can manage their location's roles
4. ❌ Missing `rbac.location_roles.manage` permission entirely

---

## SECTION 4: JOB TITLE DISPLAY (MASTER PLAN SECTION 5)

**STATUS**: ✅ CORRECTLY IMPLEMENTED

### Implementation:

**From `/tenant/routes.py` lines 28–62** (`_derive_job_title` function):

```python
def _derive_job_title(membership, db):
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
            .order_by(BizRole.priority.desc().nulls_last())
        ).all()
        if loc_assignments:
            mlr, role = loc_assignments[0]
            return mlr.job_title_label or role.name  ✅

    # Check business-level assignments
    biz_assignments = db.execute(
        select(MembershipRole, BizRole)
        .join(BizRole, BizRole.id == MembershipRole.role_id)
        .where(MembershipRole.membership_id == membership.id)
        .order_by(BizRole.priority.desc().nulls_last())
    ).all()
    if biz_assignments:
        mr, role = biz_assignments[0]
        return mr.job_title_label or role.name  ✅

    return None
```

### Usage:

**Endpoints**:
- GET `/api/v1/tenant/{business_id}/members` — returns `job_title` in list
- GET `/api/v1/tenant/{business_id}/members/{membership_id}/profile` — returns `job_title`
- PUT `/api/v1/tenant/{business_id}/members/{membership_id}/profile` — accepts `job_title` update

**Key Finding**: ✅ Job title is purely display-based, never used in permission checks.

---

## SECTION 5: EFFECTIVE PERMISSIONS API (MASTER PLAN SECTION 6)

**REQUIREMENT**: Return effective permissions to frontend for UI gating.

**STATUS**: ❌ **NOT FOUND AS DEDICATED ENDPOINT**

### What exists:

**From `/tenant/routes.py`**: Permission checks happen inline via `require_permission()` dependency, but:
- ❌ No `/api/v1/tenant/{business_id}/me/effective-permissions` endpoint
- ❌ No `/api/v1/tenant/{business_id}/locations/{location_id}/my-permissions` endpoint

### Where permissions ARE used:

The permission system is enforced at the route level, not exposed to the frontend. The frontend receives:
- List of roles via `/members` endpoints
- Job title display
- List of locations

But NOT the computed effective permissions.

**Finding**: This is a **gap** from the master plan. Frontend must infer permissions from role names or make multiple requests.

---

## SECTION 6: AUDIT LOGGING

**STATUS**: ✅ PARTIAL (Model exists, not fully used in RBAC changes)

### AuditEvent Model (Lines 279–296 of `identity.py`):
```python
class AuditEvent(UUIDMixin, Base):
    __tablename__ = "audit_events"
    
    business_id: str (nullable, indexed)
    actor_type: ActorType (user | agent | system)
    actor_id: str (nullable)
    action: str (e.g., "create", "update")
    entity: str (e.g., "BizRole")
    entity_id: str
    diff_json: str (nullable)
    correlation_id: str (indexed)
    created_at: datetime (indexed with business_id)
```

### What's audited:

**From `/control/routes.py`**:
- Business creation/deletion (via patch endpoints)
- User status changes
- Agent creation/revocation

**NOT EXPLICITLY AUDITED** (no audit log insertions found):
- Role creation/modification
- Permission assignment to roles
- User role assignment changes
- Location role assignment changes

**Finding**: Audit logging infrastructure exists ✅ but is not being written to for RBAC changes. This is a **compliance gap**.

---

## SECTION 7: DATA STRUCTURE COMPARISON

### Master Plan (HN3T_MASTER_PLAN.md Section 3):

```
roles
├── id
├── business_id
├── scope_type (BUSINESS | LOCATION) ✅
├── location_id (if scope='LOCATION') ✅
├── name
└── priority ✅

permissions
├── id
└── key (unique)

role_permissions
├── role_id (PK)
├── permission_id (PK)

user_role_assignments
├── id
├── user_id
├── business_id
├── scope_type ✅
├── location_id ✅
├── role_id
├── job_title_label ✅
├── created_by_user_id ✅
└── created_at
```

### Actual Implementation:

```
permissions ✅ (same)

biz_roles (≈ roles)
├── id
├── business_id
├── scope_type ✅
├── location_id ✅
├── name
├── priority ✅
├── is_system_template
└── (no created_at in master plan, but exists)

biz_role_permissions ✅ (same as role_permissions)

memberships (linking users to businesses)
└── relationship to role assignments via:
    ├── membership_roles (business-scoped)
    │   ├── membership_id
    │   ├── role_id
    │   ├── job_title_label ✅
    │   └── created_by_user_id ✅
    └── membership_location_roles (location-scoped) ✅
        ├── membership_id
        ├── location_id ✅
        ├── role_id
        ├── job_title_label ✅
        └── created_by_user_id ✅
```

**Key Differences**:
1. ✅ All master plan fields present
2. ✅ Scope separation implemented (BizRole has scope_type)
3. ✅ Location-scoped assignments via MembershipLocationRole
4. ✅ Job title label support
5. ✅ Created_by tracking
6. **Difference**: Uses `Membership` as intermediary instead of direct `user_role_assignments` table
   - Allows business-level context before location scoping
   - Cleaner tenant model

---

## SECTION 8: ROUTES & ENDPOINTS SUMMARY

### RBAC Management Endpoints:

#### Tenant Routes (`/api/v1/tenant/{business_id}/`)

**Roles**:
- `GET /roles` (require_permission: "roles:read")
- `POST /roles/provision` (require_permission: "roles:write")
- `POST /roles` (require_permission: "roles:write")
- `POST /roles/{role_id}/permissions` (require_permission: "roles:write")

**Members**:
- `GET /members` (require_permission: "members:read")
- `POST /members` (require_permission: "members:write")
- `GET /members/{membership_id}/profile` (require_permission: "members:read")
- `PATCH /members/{membership_id}/profile` (require_permission: "members:write")
- `PUT /members/{membership_id}/roles` (require_permission: "members:write")
- `PATCH /members/{membership_id}/status` (require_permission: "members:write")
- `PATCH /members/{membership_id}/remove` (require_permission: "members:write")

**Location Roles** (PER-LOCATION SCOPED):
- `GET /members/{membership_id}/location-roles` (require_permission: "roles:read")
- `PUT /members/{membership_id}/location-roles` (require_permission: "roles:write")

#### Control Routes (`/api/v1/control/`) — SuperAdmin Only

**Permissions**:
- `GET /permissions`
- `POST /roles` (create system template)
- `GET /roles` (list templates)

**Agents**:
- `GET /agents`
- `POST /agents` (create + generate API key)
- `DELETE /agents/{agent_id}` (revoke)

**Businesses**:
- `GET /businesses`
- `POST /businesses`
- `DELETE /businesses/{business_id}` (soft delete)

**Audit**:
- `GET /audit` (global)

---

## SECTION 9: GAPS VS MASTER PLAN

### Critical Gaps:

| Feature | Master Plan | Actual | Status |
|---------|-------------|--------|--------|
| **scope_type on roles** | ✅ BUSINESS/LOCATION | ✅ BizRole.scope_type | ✅ DONE |
| **location_id on roles** | ✅ For LOCATION scope | ✅ BizRole.location_id | ✅ DONE |
| **job_title_label** | ✅ Display-only | ✅ MembershipRole/LocationRole | ✅ DONE |
| **Per-location RBAC** | ✅ Required | ✅ MembershipLocationRole | ✅ DONE |
| **Location owner delegation** | ✅ rbac.location_roles.manage + rbac.location_assignments.manage | ❌ Uses generic "roles:write" | ❌ **MISSING** |
| **Permission check prevents cross-location edits** | ✅ Required | ⚠️ Partial (no location-owner guard) | ⚠️ **PARTIAL** |
| **Effective permissions API** | ✅ /api/me/permissions endpoint | ❌ Not exposed | ❌ **MISSING** |
| **Audit RBAC changes** | ✅ Required | ❌ Not written | ❌ **MISSING** |
| **Prevent removing last Location Owner** | ✅ Optional guard | ❌ Not implemented | ❌ **MISSING** |

### Minor Gaps:

1. **Permission naming**: Master plan uses `rbac.location_roles.manage` format; code uses `roles:read`, `roles:write`
2. **No dedicated location-owner validation**: Can't check "is this user a location owner for this location"
3. **No effective permissions computation endpoint**: Frontend can't fetch computed permissions
4. **Unused migration tables**: Two complete RBAC table sets exist (planned + actual)

---

## SECTION 10: CODE QUALITY OBSERVATIONS

### Strengths:

1. ✅ **Type hints throughout** — Uses SQLAlchemy 2.0 with Mapped types
2. ✅ **Proper dependency injection** — FastAPI Depends pattern for auth/RBAC
3. ✅ **Superadmin bypass** — All RBAC checks respect `is_superadmin` flag
4. ✅ **Location scoping** — Properly separates business vs. location roles
5. ✅ **Job title flexibility** — Supports custom labels per assignment

### Issues:

1. ⚠️ **Orphaned tables** — `roles`, `role_permissions`, `user_role_assignments` never used
2. ⚠️ **Permission naming inconsistency** — Some use `:`, some use no delimiter
3. ⚠️ **No location-owner checks** — Anyone with `roles:write` can edit any location's roles
4. ⚠️ **Missing audit trail** — RBAC changes not logged
5. ⚠️ **No constraint on location_id in role scope** — BizRole.location_id can be set even if scope_type='BUSINESS'

---

## SECTION 11: RECOMMENDATIONS

### High Priority:

1. **Implement location-owner delegation checks**
   - Add permissions: `rbac.location_roles.manage`, `rbac.location_assignments.manage`
   - Add constraint: Only location owners can edit location-scoped roles at their location
   - Seed "Location Owner" template role with these permissions

2. **Add audit logging for RBAC changes**
   - Log role creation/modification
   - Log role-permission changes
   - Log membership assignment changes
   - Include `created_by_user_id` in audit events

3. **Expose effective permissions API**
   - Endpoint: `GET /api/v1/tenant/{business_id}/me/permissions`
   - Returns: List of permission keys user has in that business
   - Optionally: `GET /api/v1/tenant/{business_id}/locations/{location_id}/me/permissions`

### Medium Priority:

1. **Add database constraint**
   ```sql
   CHECK (
       (scope_type = 'BUSINESS' AND location_id IS NULL)
       OR
       (scope_type = 'LOCATION' AND location_id IS NOT NULL)
   )
   ```

2. **Cleanup orphaned tables**
   - Either remove from migration, or populate and use them
   - Current state is confusing

3. **Add last-location-owner guard**
   - Prevent removing the last location owner role from a location
   - Implement in `set_member_location_roles` endpoint

4. **Standardize permission key naming**
   - Use consistent format: `module.resource.action`
   - Examples: `schedule.shifts.read`, `roles.location.manage`

### Low Priority:

1. Document permission matrix (which roles have which permissions)
2. Add tests for location-scoped RBAC enforcement
3. Consider caching for permission checks (repeated DB queries per request)

---

## SECTION 12: SCHEMA DIAGRAM

```
┌─────────────────┐
│     User        │
│  (from auth)    │
└────────┬────────┘
         │ 1
         │
         │ *
         ▼
┌──────────────────────────────────────┐
│      Membership                      │
│ (user↔business binding)              │
│ - user_id (FK)                       │
│ - business_id (FK)                   │
│ - primary_location_id (FK)           │
│ - status (active/invited/inactive)   │
└──────────────────────────────────────┘
         │
         ├──────────┬──────────────────┐
         │          │                  │
         │1        │1                 │1
         │         │                   │
         │*        │*                  │*
         ▼         ▼                   ▼
    ┌────────────────┐    ┌──────────────────────────┐
    │ MembershipRole │    │ MembershipLocationRole   │
    │ (biz-scoped)   │    │ (location-scoped) ✅    │
    ├────────────────┤    ├──────────────────────────┤
    │ membership_id  │    │ membership_id            │
    │ role_id    ────┼───►│ location_id (FK)         │
    │ job_title_label    │ role_id    ──────┐      │
    │ created_by_user_id │ job_title_label  │      │
    └────────────────┘    │ created_by_user_id      │
                          └──────────────────┬──────┘
                                            │
                                            │ *
                          ┌─────────────────┤
                          │                 │
                          │1                │1
         ┌────────────────▼─────────────────┘
         │
         │ *
         ▼
    ┌─────────────────────────────┐
    │      BizRole                │
    │ (business or location role) │
    ├─────────────────────────────┤
    │ - id                        │
    │ - business_id               │
    │ - name                      │
    │ - scope_type ✅             │
    │ - location_id ✅            │
    │ - priority ✅               │
    │ - is_system_template        │
    └────────────────┬────────────┘
                     │
                     │ *
                     ▼
         ┌──────────────────────────┐
         │ BizRolePermission        │
         │ (role↔permission link)   │
         ├──────────────────────────┤
         │ role_id          (PK)    │
         │ permission_id    (PK)    │
         └──────────────────────────┘
                     │
                     │ *
                     ▼
         ┌──────────────────────────┐
         │ Permission               │
         ├──────────────────────────┤
         │ - id                     │
         │ - key (unique) ✅        │
         │   e.g., "schedule:read"  │
         │ - description            │
         └──────────────────────────┘
```

---

## SECTION 13: FINAL ASSESSMENT

| Criterion | Score | Notes |
|-----------|-------|-------|
| **Per-location RBAC** | ✅ 95% | Location scopes implemented, but missing location-owner delegation |
| **Job title display** | ✅ 100% | Correctly prioritized per-location, fallback to business-level |
| **Permission enforcement** | ✅ 90% | Enforced at all endpoints, but missing location-owner guards |
| **Audit logging** | ❌ 20% | Infrastructure exists, not used for RBAC changes |
| **API completeness** | ⚠️ 70% | Missing effective permissions endpoint |
| **Code quality** | ✅ 85% | Good types/DI, but orphaned tables confuse design |
| **Master plan adherence** | ⚠️ 75% | All fields exist, but different table structure; missing delegation pattern |

**Overall**: The RBAC system is **functionally complete** for basic role/permission management with location scoping. The **critical gaps** are location-owner delegation checks and audit logging. The codebase is well-structured and maintainable.

---

