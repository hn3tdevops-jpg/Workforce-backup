# Silver Sands → Hospitable/Workforce Integration Plan

## Goal
Integrate the Silver Sands operations blueprint and website prototype into the existing **Hospitable / Workforce** platform as a location-scoped housekeeping operations module.

This should become a first-class operational area inside the current multi-tenant system rather than a separate app.

---

## 1. Product Positioning Inside Workforce

### Existing platform role
Workforce remains the system of record for:
- businesses
- locations
- employees
- schedules
- timeclock
- RBAC / permissions

### New Hospitable module role
Hospitable becomes the operational layer for:
- property hierarchy
- rooms / units
- room statuses
- housekeeping assignments
- inspections
- maintenance issues
- room assets and inventory expectations
- bulk room operations
- property dashboards

Silver Sands should be modeled as:
- **Business**: Silver Sands Motel
- **Location**: Silver Sands main property
- **Module**: Hospitable / Housekeeping Ops

---

## 2. Data Model Mapping

The uploaded blueprint uses a simple structure:

Property → Building → Floor → Sector → Room

In Workforce/Hospitable, implement it with normalized tables and location scoping.

### Recommended tables

#### property_buildings
- id
- location_id (FK locations.id)
- code (`B1`)
- name (`Building 1`)
- sort_order
- is_active
- created_at
- updated_at

#### property_floors
- id
- building_id (FK property_buildings.id)
- floor_number
- label (`Floor 1`)
- sort_order
- created_at
- updated_at

#### property_sectors
- id
- floor_id (FK property_floors.id)
- code (`north`, `south`)
- name (`North Side`, `South Side`)
- description
- sort_order
- created_at
- updated_at

#### hk_room_groups
- id
- location_id (FK locations.id)
- name (`North Group`, `South Group`)
- color
- description
- created_at
- updated_at

#### hk_rooms
- id
- location_id (FK locations.id)
- building_id (FK property_buildings.id)
- floor_id (FK property_floors.id)
- sector_id (FK property_sectors.id)
- room_group_id (FK hk_room_groups.id, nullable)
- room_number (string, not int; safer for future values like `101A`)
- room_label
- room_type
- bed_count
- bed_type_summary
- floor_surface (`carpet`, `hardwood`, `mixed`)
- housekeeping_status
- occupancy_status
- inspection_status
- maintenance_status
- out_of_order_reason
- notes
- last_cleaned_at
- last_inspected_at
- is_active
- created_at
- updated_at

#### hk_room_assets
Tracks installed/fixed items per room.
- id
- room_id
- asset_type (`tv`, `lamp`, `fridge`, `microwave`, `coffee_maker`, `hvac`, etc.)
- asset_name
- quantity_expected
- quantity_present
- condition_status
- maintenance_notes
- created_at
- updated_at

#### hk_room_supply_pars
Tracks expected room setup/par levels.
- id
- room_id
- item_code
- item_name
- expected_qty
- min_qty
- unit
- created_at
- updated_at

#### hk_tasks
- id
- location_id
- room_id nullable
- task_type (`clean_checkout`, `clean_stayover`, `inspection`, `restock`, `maintenance_followup`)
- title
- description
- priority
- status (`open`, `assigned`, `in_progress`, `done`, `cancelled`)
- assigned_user_id nullable
- due_at nullable
- completed_at nullable
- created_by_user_id nullable
- created_at
- updated_at

#### hk_task_events
Audit/status history.
- id
- task_id
- event_type
- from_status
- to_status
- notes
- created_by_user_id nullable
- created_at

#### maintenance_issues
- id
- location_id
- room_id nullable
- issue_type
- title
- description
- severity
- status (`open`, `triaged`, `in_progress`, `resolved`, `closed`)
- assigned_user_id nullable
- reported_by_user_id nullable
- reported_at
- resolved_at nullable
- created_at
- updated_at

#### hk_room_status_events
Operational room history.
- id
- room_id
- event_type (`housekeeping_status_changed`, `inspection_status_changed`, `maintenance_flag_changed`, `note_added`)
- old_value
- new_value
- notes
- created_by_user_id nullable
- created_at

---

## 3. Status Model

The Silver Sands prototype already implies a usable room flow.

### Housekeeping status
Recommended enum:
- `dirty`
- `assigned`
- `cleaning`
- `clean`
- `inspect`
- `inspected`
- `blocked`

### Maintenance status
Recommended enum:
- `ok`
- `issue`
- `in_progress`
- `resolved`

### Occupancy status
Recommended enum:
- `vacant`
- `occupied`
- `checkout`
- `stayover`
- `ooo` (out of order)

### Inspection status
Recommended enum:
- `not_required`
- `pending`
- `passed`
- `failed`

This lets the platform distinguish guest state from housekeeping state.

---

## 4. Seed Silver Sands Layout

Seed the initial known structure from the blueprint.

### Buildings / floors / sectors
- Building 1
- Floor 1
- North Side Sector
- South Side Sector

### Room groups
- North Group: 7, 8, 9, 10, 11, 12
- South Group: 1, 2, 3, 4, 5, 6

### Initial room seed set
South:
- 1, 2, 3, 4, 5, 6

North:
- 7, 8, 9, 10, 11, 12

Important: in Workforce/Hospitable, use **location-aware seeders** instead of raw one-off SQL.

---

## 5. API Surface

Add a dedicated router namespace, for example:
- `/api/v1/hospitable/...`

### Suggested endpoints

#### Property structure
- `GET /hospitable/locations/{location_id}/property-tree`
- `POST /hospitable/buildings`
- `POST /hospitable/floors`
- `POST /hospitable/sectors`

#### Rooms
- `GET /hospitable/rooms`
- `POST /hospitable/rooms`
- `GET /hospitable/rooms/{room_id}`
- `PATCH /hospitable/rooms/{room_id}`
- `POST /hospitable/rooms/bulk-status`
- `POST /hospitable/rooms/bulk-assign-group`
- `POST /hospitable/rooms/import-layout`

#### Housekeeping tasks
- `GET /hospitable/tasks`
- `POST /hospitable/tasks`
- `PATCH /hospitable/tasks/{task_id}`
- `POST /hospitable/tasks/{task_id}/assign`
- `POST /hospitable/tasks/{task_id}/complete`

#### Maintenance
- `GET /hospitable/maintenance/issues`
- `POST /hospitable/maintenance/issues`
- `PATCH /hospitable/maintenance/issues/{issue_id}`

#### Inventory / room assets
- `GET /hospitable/rooms/{room_id}/assets`
- `POST /hospitable/rooms/{room_id}/assets`
- `GET /hospitable/rooms/{room_id}/supply-pars`
- `POST /hospitable/rooms/{room_id}/supply-pars`

#### Dashboards
- `GET /hospitable/dashboard/summary?location_id=...`
- `GET /hospitable/dashboard/housekeeping-board?location_id=...`
- `GET /hospitable/dashboard/maintenance-board?location_id=...`

---

## 6. RBAC / Permissions

Use the existing Workforce RBAC model with location scoping.

### New permissions
- `hospitable.rooms.read`
- `hospitable.rooms.write`
- `hospitable.rooms.bulk_update`
- `hospitable.tasks.read`
- `hospitable.tasks.write`
- `hospitable.assignments.manage`
- `hospitable.inspections.perform`
- `hospitable.maintenance.read`
- `hospitable.maintenance.write`
- `hospitable.inventory.read`
- `hospitable.inventory.write`
- `hospitable.dashboard.read`
- `hospitable.config.manage`

### Example roles
- Property Owner
- General Manager
- Housekeeping Manager
- Housekeeper
- Inspector
- Maintenance Tech

All permissions should remain **business/location filtered**.

---

## 7. UI Integration

The uploaded website should be treated as a **UI prototype**, not the production architecture.

### Convert the prototype into Workforce pages/modules
Prototype pages map cleanly to Workforce sections:
- Dashboard → Hospitable Overview
- Rooms → Room Directory / Room Board
- Housekeeping → Housekeeping Queue / Assignments
- Maintenance → Maintenance Board
- Inventory → Room Supply Standards / Restock Tracking
- Settings → Location Hospitable Settings

### Recommended production UI structure
Inside the Workforce nav:
- Operations
  - Hospitable Dashboard
  - Rooms
  - Housekeeping Board
  - Inspections
  - Maintenance
  - Inventory Standards
  - Reports
  - Property Setup

### Important UI changes from the prototype
The current prototype stores everything in localStorage. Replace that with:
- API-backed data loading
- optimistic updates where useful
- location selector from Workforce context
- role-aware actions
- audit-friendly action logging

### Useful production views
1. **Room Board**
   - cards or table grouped by sector/group
   - quick status chips
   - bulk selection
   - assign / change status / add issue

2. **Housekeeping Dispatch Board**
   - unassigned tasks
   - tasks by employee
   - today’s clean/inspect workload

3. **Maintenance Triage Board**
   - open issues by severity
   - room linkage
   - status aging

4. **Property Setup View**
   - building/floor/sector editor
   - room import wizard
   - asset template editor

---

## 8. Implementation Sequence

### Phase A — Foundation
1. Add Hospitable module permission set
2. Add new SQLAlchemy models
3. Create Alembic migrations
4. Build seed script for Silver Sands location structure
5. Add Pydantic schemas

### Phase B — Core room operations
1. Room CRUD
2. Property tree API
3. Bulk room status updates
4. Room event logging
5. Dashboard summary API

### Phase C — Housekeeping workflow
1. Housekeeping task model
2. Assignment flow
3. Status transition validation
4. Employee-based task board
5. Inspection workflow

### Phase D — Maintenance and room assets
1. Maintenance issues CRUD
2. Room asset tracking
3. Supply par tracking
4. Room detail page with operational history

### Phase E — UI port from Silver Sands prototype
1. Convert layout/theme into Workforce design system
2. Build dashboard
3. Build room board
4. Build housekeeping board
5. Build maintenance board
6. Build settings/property setup

---

## 9. Validation Rules

### Recommended constraints
- unique room number per location
- sector must belong to floor
- floor must belong to building
- building must belong to location
- room group must belong to same location as room
- blocked / out-of-order rooms cannot be assigned standard cleaning tasks without override
- room housekeeping status transitions should be validated through a service layer

### Example transitions
- `dirty -> assigned`
- `assigned -> cleaning`
- `cleaning -> clean`
- `clean -> inspect`
- `inspect -> inspected`
- any state -> `blocked` with reason

---

## 10. Seed Data from Uploaded Blueprint

The following should be seeded first:

### property_buildings
- Building 1

### property_floors
- Floor 1 under Building 1

### property_sectors
- North Side Sector
- South Side Sector

### hk_room_groups
- North Group
- South Group

### hk_rooms
- South 1 through 6
- North 7 through 12

### Starter room assets template
For each room, seed optional asset records for:
- TV
- fridge
- microwave
- coffee maker
- heater/AC

### Starter supply par template
For each room, configurable expected quantities for:
- towels
- hand towels
- washcloths
- sheets
- pillowcases
- blankets
- trash bags
- soap
- shampoo

---

## 11. Copilot-Ready Build Instruction

Use this as the implementation instruction inside the Workforce repo:

> Build a new location-scoped `Hospitable` module inside Workforce for motel/hotel housekeeping operations. Use the existing multi-tenant architecture, RBAC, location scoping, SQLAlchemy async models, Alembic migrations, and existing API conventions. Implement normalized property hierarchy tables (building, floor, sector), room groups, rooms, housekeeping tasks, maintenance issues, room assets, supply par levels, and audit/event tables. Seed Silver Sands Motel layout for Building 1 / Floor 1 / North + South sectors / rooms 1-12. Expose CRUD + dashboard + bulk room update endpoints. Port the Silver Sands website prototype into Workforce UI pages using API-backed state rather than localStorage.

---

## 12. What Not To Do

- do not make Silver Sands a separate standalone app
- do not store production state in browser localStorage
- do not hardcode motel-specific assumptions into global code paths
- do not bypass the Workforce location/business permission system
- do not model room numbers as integer-only values

---

## 13. Recommended First Deliverable

The first merged PR should include:
- migrations
- SQLAlchemy models
- seed command for Silver Sands
- room list API
- bulk housekeeping status API
- dashboard summary API
- basic room board UI

That gives immediate operational value while preserving room for inspections, maintenance, and inventory expansion.
