# 🏗 UNIFIED WORKFORCE + HOSPITABLE OPS MASTER ARCHITECTURE

This document is the single cohesive architecture plan combining:

- Workforce Platform (RBAC, Tenancy, UI System)
- Hospitable Ops (Housekeeping Operations)
- Location-Scoped Permissions
- Integration Contracts
- Backend Architecture
- Frontend Architecture
- State Machines
- Idempotency & Offline Support
- Deployment & Phase Build Order

======================================================================
FULL ARCHITECTURE SPECIFICATION
======================================================================

# UNIFIED MASTER PLAN
# Workforce + Hospitable Ops + RBAC + UI + Integration



# Workforce Cloud System — Unified Architecture & Implementation Master Plan

This document merges all prior planning into a single structured implementation guide covering:

- Multi-tenant backend control plane
- Tenant / Worker / Agent planes
- Per-location RBAC with delegated location owners
- Job title as display-only value
- UI architecture (dark theme, business selector, collapsible nav, navigation IA)
- Authorization rules
- API structure
- Implementation order
- Guardrails and hard constraints

======================================================================
SECTION 1 — SYSTEM ARCHITECTURE OVERVIEW
======================================================================

The platform consists of 4 logical planes operating on one backend:

1) CONTROL PLANE (Platform Admin)
   - Cross-tenant management
   - Business provisioning
   - Global audit logs
   - Permission templates
   - Agent registry & credentials
   - Data export/import tools

2) TENANT PLANE (Business Owners / Managers)
   - Employees
   - Roles & Permissions
   - Location-scoped access
   - Scheduling
   - Reports
   - Integrations

3) WORKER PLANE (Employees)
   - My schedule
   - Time clock
   - Requests
   - Profile display (job title per location)

4) AGENT PLANE (AI agents / integrations)
   - API key credentials
   - Explicit scoped permissions
   - Run tracking + logs
   - Least privilege enforcement

Design rule:
One backend. Different scopes. UI only reflects what backend policy allows.

======================================================================
SECTION 2 — MULTI-TENANCY MODEL
======================================================================

Core Entities:

Business
- id
- name
- settings_json

Location
- id
- business_id
- name
- timezone
- settings_json

User
- id
- email
- status

Every tenant-owned table must include:
- business_id
- optional location_id where relevant

======================================================================
SECTION 3 — PER-LOCATION RBAC MODEL (FINALIZED DESIGN)
======================================================================

CORE PRINCIPLES:
- Permissions come ONLY from Roles.
- Roles can be BUSINESS-scoped or LOCATION-scoped.
- Users can have different Roles at different Locations.
- Job Title is display-only and stored on assignment.

------------------------------------
TABLES
------------------------------------

roles
- id
- business_id
- scope_type ENUM('BUSINESS','LOCATION')
- location_id NULL (required if scope='LOCATION')
- name
- priority INT DEFAULT 0

permissions
- id
- key (unique)  example: 'employees.read'

role_permissions
- role_id
- permission_id
(unique pair)

user_role_assignments  (CRITICAL TABLE)
- id
- user_id
- business_id
- scope_type ENUM('BUSINESS','LOCATION')
- location_id NULL (required if scope='LOCATION')
- role_id
- job_title_label NULL
- created_by_user_id
- created_at

------------------------------------
CONSTRAINTS
------------------------------------

- LOCATION scope requires location_id
- BUSINESS scope must not have location_id
- Assignment scope must match role scope
- Role business_id must match assignment business_id
- Prevent duplicate assignments (unique composite key)
- Enforce tenant scoping everywhere

------------------------------------
AUTHORIZATION RULE
------------------------------------

User can perform action X at location L if:

EXISTS assignment WHERE:
    (
        scope_type = 'BUSINESS'
        AND role includes permission_key
    )
    OR
    (
        scope_type = 'LOCATION'
        AND location_id = L
        AND role includes permission_key
    )

IMPORTANT:
job_title_label is NEVER used in permission checks.

======================================================================
SECTION 4 — LOCATION OWNER DELEGATED MANAGEMENT
======================================================================

System Role:
"Location Owner" (LOCATION scoped)

Permissions:
- rbac.location_roles.manage
- rbac.location_assignments.manage

Rules:
Only users with those permissions at that location may:
- Create/edit LOCATION roles for that location
- Assign/revoke roles at that location

Cannot:
- Modify roles outside their location
- Grant business-wide roles unless explicitly allowed

Optional guard:
Prevent removing last Location Owner at a location.

======================================================================
SECTION 5 — PROFILE PAGE / JOB TITLE DISPLAY
======================================================================

Job title is NOT a separate system.
It is stored in user_role_assignments.job_title_label.

For a given location context:

1) Fetch LOCATION assignments for that user at location.
2) Choose primary:
   - highest roles.priority
3) Display:
   job_title = job_title_label if set else role.name
4) Optionally list secondary roles.

Never use job_title for authorization.

======================================================================
SECTION 6 — EFFECTIVE PERMISSIONS COMPUTATION
======================================================================

Given selected business_id and location_id:

effective_permissions =
    UNION(
        permissions from BUSINESS assignments,
        permissions from LOCATION assignments at location
    )

Returned to frontend for UI gating.
Backend remains source of truth.

======================================================================
SECTION 7 — API STRUCTURE
======================================================================

/api/v1/auth/*
/api/v1/control/*
/api/v1/tenant/*
/api/v1/worker/*
/api/v1/agent/*

RBAC endpoints:

GET  /api/rbac/locations/{location_id}/roles
POST /api/rbac/locations/{location_id}/roles
PATCH /api/rbac/locations/{location_id}/roles/{role_id}
DELETE /api/rbac/locations/{location_id}/roles/{role_id}

GET  /api/rbac/locations/{location_id}/assignments
POST /api/rbac/locations/{location_id}/assignments
DELETE /api/rbac/locations/{location_id}/assignments/{assignment_id}

Profile endpoint:
GET /api/locations/{location_id}/users/{user_id}/profile

======================================================================
SECTION 8 — UI / FRONTEND IMPLEMENTATION PLAN
======================================================================

-------------------------------------------------
1) DARK THEME SYSTEM
-------------------------------------------------

Use CSS variables (design tokens).

Minimum tokens:
--bg
--bg-elevated
--text
--text-muted
--border
--primary
--primary-contrast
--success
--warning
--danger
--nav-bg
--nav-text
--nav-active

Toggle:
document.documentElement.dataset.theme = "dark"

Persist:
localStorage + optional users.theme_pref

Acceptance:
All pages readable
Status colors distinct
Tables/forms consistent contrast

-------------------------------------------------
2) BUSINESS SELECTOR
-------------------------------------------------

Endpoint:
GET /api/me/businesses
Returns: [{id, name, is_default}]

Frontend:
Display name
Value = id
Persist selected business_id

Never show raw IDs in UI.

-------------------------------------------------
3) COLLAPSIBLE NAVBAR
-------------------------------------------------

Desktop:
Expanded = icons + labels
Collapsed = icons only + tooltips

Mobile:
Hamburger drawer

Persist collapsed state in localStorage.

-------------------------------------------------
4) NAVIGATION IA (GROUPED)
-------------------------------------------------

Overview
Operations
People
Inventory
Scheduling
Reports
Admin / Setup

Rules:
- Only show items user has permission for.
- Filter by selected business + location.
- Highlight active section.

======================================================================
SECTION 9 — IMPLEMENTATION ORDER
======================================================================

1. Multi-tenant structure
2. RBAC core
3. Location owner delegation
4. Profile display logic
5. Effective permissions API
6. Business selector fix
7. Navigation regrouping + RBAC filtering
8. Collapsible nav
9. Dark theme tokens
10. Audit logging hardening

======================================================================
SECTION 10 — HARD GUARDRAILS
======================================================================

DO NOT:
- Use job_title in permission checks
- Allow cross-location role editing without permission
- Skip tenant scoping in queries

ALWAYS:
- Validate scope_type matches role
- Validate business_id consistency
- Audit role and assignment changes
- Enforce least privilege

======================================================================
SUCCESS DEFINITION
======================================================================

- Clean multi-tenant backend
- Per-location delegated RBAC
- Job title purely display-based
- UI reflects permissions dynamically
- Fully auditable role & assignment changes
- Agent permissions isolated and scoped



# 🏨 HOSPITABLE — COPILOT MASTER PLAN (Single Source of Truth)

## Housekeeping Operations + Workforce Integration (Scheduling/Timeclock)

### Objective
Build **Hospitable Ops** (new) as a location-scoped housekeeping operations platform that integrates with an existing **Workforce** system (employees/schedules/timeclock). Workforce remains the **system of record** for employees, shifts, and labor tracking.

Hospitable Ops manages:
- Units/Rooms, Task lifecycle, Inspections, Issues/Maintenance holds
- Checklist templates & execution
- Event logs + audit
- Shift-aware auto-assignment
- Offline execution support (frontend queue + backend idempotency)

---

## 0) SYSTEM ARCHITECTURE PRINCIPLES

### Separation of concerns

**Workforce (existing, authoritative)**
- Employees (source of truth)
- Shifts / schedules (source of truth)
- Timeclock / labor tracking

**Hospitable Ops (new)**
- Units / Rooms / Spaces
- Housekeeping tasks (checkout/stayover/deep clean)
- Inspections workflow
- Issues/Maintenance holds
- Checklists
- Event & audit log
- Auto-assignment engine (uses Workforce shifts)
- Offline execution mode (queue + replay)

### Integration rule
- Do **NOT** implement scheduling or timeclock in Hospitable Ops.
- Store references only (`external_employee_id`, `external_shift_id`).
- Fetch roster/shifts via Workforce REST API (httpx client).

---

## 1) BACKEND — `hospitable-ops` (FastAPI)

### Stack (use exactly)
- Python 3.12
- FastAPI + Uvicorn
- SQLAlchemy 2.0 **async**
- asyncpg
- Alembic
- Pydantic v2
- python-jose (JWT)
- passlib[bcrypt]
- httpx
- Postgres
- Docker Compose
- pytest + pytest-asyncio

### Project structure (Copilot must follow)

```
hospitable-ops/
  app/
    main.py
    core/
      config.py
      security.py
      rbac.py
      deps.py
      idempotency.py
    db/
      session.py
      base.py
      migrations/            # alembic
    models/
      tenant.py
      rbac.py
      housekeeping.py
      checklists.py
      integrations.py
      events.py
      idempotency.py
    schemas/
      auth.py
      tenant.py
      units.py
      tasks.py
      inspections.py
      issues.py
      checklists.py
      integrations.py
      events.py
    services/
      units.py
      tasks.py
      inspections.py
      issues.py
      checklists.py
      auto_assign.py
      integrations_workforce.py
      events.py
    api/
      routes/
        auth.py
        bootstrap.py
        units.py
        tasks.py
        inspections.py
        issues.py
        checklists.py
        integrations.py
        events.py
  tests/
  docker-compose.yml
  alembic.ini
  pyproject.toml
```

---

## 2) DOMAIN MODEL — Nodes, Edges, State Machines

All domain records are **location-scoped**. All status transitions must:
1. Validate transition
2. Update entity
3. Insert event(s) (`TaskStatusEvent` + `AuditEvent`)

---

## 3) CORE TENANCY (Location Scoped)

### Business
- id (UUID PK)
- name
- created_at

### Location
- id (UUID PK)
- business_id (FK)
- name
- address
- created_at

**Constraint:** every Unit/Task/Issue/ChecklistTemplate/Event includes `location_id`.

---

## 4) RBAC (Location-Scoped)

### Role
- id (UUID PK)
- name

### Permission
- id (UUID PK)
- key (string unique) e.g. `housekeeping.tasks.assign`

### RolePermission
- role_id (FK)
- permission_id (FK)
- **Unique(role_id, permission_id)**

### User
- id (UUID PK)
- email (unique)
- hashed_password
- is_active
- created_at

### UserLocationRole
- user_id (FK)
- location_id (FK)
- role_id (FK)
- **Unique(user_id, location_id, role_id)**

### Enforcement
Every request must pass:
- auth (JWT)
- location membership (`UserLocationRole` exists for location)
- permission check (role → permissions)

Permission examples:
- housekeeping.units.read / update
- housekeeping.tasks.read / assign / update
- housekeeping.inspections.create
- housekeeping.issues.create / update
- admin.bootstrap
- admin.locations.manage
- admin.users.manage

---

## 5) HOUSEKEEPING CORE

### 5.1 Units (Rooms/Spaces)

`Unit.status` enum:
- DIRTY
- ASSIGNED
- IN_PROGRESS
- CLEANED
- INSPECTED
- READY
- OUT_OF_ORDER
- DND
- LATE_CHECKOUT
- MAINTENANCE_HOLD

Fields:
- id (UUID PK)
- location_id (FK)
- label (string; room # / name)
- type (guest/public/service)
- notes (text)
- status (enum)
- created_at

**Constraints**
- Unique(location_id, label)

Optional add-ons (ok to add now)
- floor (string)
- coordinates_json (for map polygons later)
- metadata_json (beds/baths/etc)

### 5.2 Tasks

`Task.status` enum:
- OPEN
- ASSIGNED
- IN_PROGRESS
- COMPLETED
- INSPECTED
- CANCELED

Fields:
- id (UUID PK)
- location_id (FK)
- unit_id (FK)
- date (DATE)
- type (checkout, stayover, deep_clean)
- status (enum)
- assigned_external_employee_id (string nullable)
- external_shift_id (string nullable)
- due_at (datetime nullable)
- started_at (datetime nullable)
- completed_at (datetime nullable)
- created_at

**Constraints**
- Index(location_id, date, status)
- Unique(location_id, unit_id, date, type)  # prevent daily duplicate generation

### 5.3 Inspections
- id (UUID PK)
- task_id (FK unique if 1 inspection per task; otherwise allow multiple)
- passed (bool)
- notes (text)
- created_by (user_id FK)
- created_at

Rule:
- If passed == true: set task INSPECTED; optionally set unit READY
- If passed == false: task stays COMPLETED (or returns to IN_PROGRESS depending on policy)

### 5.4 Issues

`Issue.status` enum:
- OPEN
- ACKNOWLEDGED
- IN_PROGRESS
- RESOLVED
- CLOSED

Fields:
- id (UUID PK)
- location_id (FK)
- unit_id (FK)
- category (string)
- severity (low/med/high)
- description (text)
- status (enum)
- created_by (user_id FK)
- created_at
- updated_at

---

## 6) CHECKLIST SYSTEM (Iteration 2)

### ChecklistTemplate
- id (UUID PK)
- location_id (FK)
- name
- version (int)
- is_active (bool)
- created_at

### ChecklistTemplateItem
- id (UUID PK)
- template_id (FK)
- label
- required (bool)
- sort_order (int)

### ChecklistRun
- id (UUID PK)
- task_id (FK)
- template_id (FK)
- started_at
- completed_at

### ChecklistRunItem
- id (UUID PK)
- run_id (FK)
- template_item_id (FK)
- status (PASS, FAIL, NA)
- notes (text)
- updated_at

Rule:
- ChecklistRun locks when completed_at set.
- ChecklistRunItem updates are rejected when run is locked.

---

## 7) INTEGRATION LAYER (Workforce)

### Tables (references only)

#### EmployeeRef
- id (UUID PK)
- location_id (FK)
- external_employee_id (string)
- display_name (string)
- **Unique(location_id, external_employee_id)**

#### ShiftRef
- id (UUID PK)
- location_id (FK)
- external_shift_id (string)
- external_employee_id (string)
- start_at (datetime)
- end_at (datetime)
- **Unique(location_id, external_shift_id)**

### Integration endpoints (Ops receives upserts)
- POST `/integrations/scheduling/employees.upsert`
- POST `/integrations/scheduling/shifts.upsert`
- GET  `/integrations/scheduling/health`

### Workforce client (httpx) used by Ops
- `fetch_roster(date, location_id)` → list employees
- `fetch_shifts(date, location_id)` → list shifts

Note: Upsert endpoints allow Workforce → Ops push, client supports Ops → Workforce pull. Either mode OK.

---

## 8) EVENT LOGGING (CRITICAL)

### TaskStatusEvent
- id (UUID PK)
- task_id (FK)
- old_status
- new_status
- changed_by (user_id FK nullable if system)
- timestamp

### AuditEvent
- id (UUID PK)
- location_id (FK)
- actor_user_id (FK nullable if system)
- entity_type (string)
- entity_id (UUID/string)
- action (string)
- payload_json (jsonb)
- timestamp

Rule: Every mutation inserts AuditEvent. Every task status change inserts TaskStatusEvent.

---

## 9) STATE MACHINES (ENFORCE)

### Unit status allowed transitions (example policy)
- DIRTY → ASSIGNED → IN_PROGRESS → CLEANED → INSPECTED → READY
- Any → OUT_OF_ORDER
- Any → MAINTENANCE_HOLD
- READY → DIRTY (after checkout event / daily reset)
- DND/LATE_CHECKOUT are flags that can block assignment or generation rules

### Task status allowed transitions
- OPEN → ASSIGNED → IN_PROGRESS → COMPLETED → INSPECTED
- OPEN/ASSIGNED/IN_PROGRESS → CANCELED
- COMPLETED can return to IN_PROGRESS if inspection fails (policy toggle)

These rules are validated in service layer, not routes.

---

## 10) BACKEND — CORE ENDPOINTS

### Auth
- POST `/auth/register`
- POST `/auth/login`
- GET  `/me`

---

### Phase 2 — Authentication & Authorization (CURRENT STATUS: PARTIAL / IMPLEMENTED)

Status: The core JWT auth flow and auth endpoints are already implemented in this repository. See:
- workforce/app/core/security.py (JWT helpers, token creation/verification)
- workforce/app/api/v1/auth/routes.py (login/register/refresh endpoints)

Action: Mark the following checklist items as COMPLETE:
- [x] JWT access + refresh token logic
- [x] Auth endpoints (login / refresh / register)
- [x] Refresh token storage (where implemented)

Remaining / optional items:
- [ ] Harden refresh-token rotation and storage to match production policy (if desired)
- [ ] Add integration tests for refresh-token rotation (optional)
- [ ] Audit and document auth config and env variables in README

Implementation note: If Phase 2 in this master plan was intended for a different/new codebase, add an explicit note to avoid confusion: "Note: phase tasks here are scoped to new modules. Existing `workforce/` implementation is considered baseline and excluded from new work."

---

### Bootstrap
- POST `/bootstrap`
  - Allowed only if **no users exist**
  - Creates first business/location/admin user/role/permissions

### Units
- POST `/locations/{location_id}/units`
- GET  `/locations/{location_id}/units`
- PATCH `/units/{unit_id}`
- POST `/units/{unit_id}/status` (transition with validation)

### Tasks
- POST `/locations/{location_id}/tasks/generate` (date + type rules; prevent dupes)
- GET  `/locations/{location_id}/tasks` (filters: date/status/assignee/unit)
- POST `/tasks/{task_id}/assign`
- POST `/tasks/{task_id}/start`
- POST `/tasks/{task_id}/complete`
- POST `/tasks/{task_id}/cancel`

### Inspections
- POST `/tasks/{task_id}/inspect`

### Issues
- POST  `/locations/{location_id}/issues`
- PATCH `/issues/{issue_id}`

### Checklists
- POST `/locations/{location_id}/checklists/templates`
- GET  `/locations/{location_id}/checklists/templates`
- POST `/tasks/{task_id}/checklists/run`
- POST `/tasks/{task_id}/checklists/run/items` (updates)

### Events
- GET `/tasks/{task_id}/events` (TaskStatusEvents)
- GET `/locations/{location_id}/audit` (admin/manager permission)

---

## 11) OFFLINE MODE SUPPORT (Backend)

### Idempotency
- Accept header: `X-Idempotency-Key`
- Store processed keys to prevent duplicate mutations.

#### IdempotencyKey table
- id (UUID PK)
- location_id
- key (string)
- request_hash (string)
- response_status (int)
- response_body_json (jsonb)
- created_at

Rule:
- For mutating endpoints: if key exists return stored response.
- Ensure TaskStatusEvent/AuditEvent tolerate replay (idempotency prevents duplicates).

---

## 12) AUTO-ASSIGNMENT ENGINE

### Inputs
- ShiftRefs for date/location
- Unassigned tasks for date/location

### Algorithm
1. Fetch ShiftRefs for date
2. Fetch tasks where status in (OPEN) (or OPEN + ASSIGNED?) and no assignee
3. Sort tasks by `(due_at NULLS LAST, unit.label)`
4. Compute weights by shift duration minutes
5. Weighted round-robin assignment to external_employee_id
6. Preview mode returns proposed assignments without committing
7. Execute mode commits assignments through service (creates AuditEvent)

Endpoints
- POST `/locations/{location_id}/auto-assign/preview`
- POS