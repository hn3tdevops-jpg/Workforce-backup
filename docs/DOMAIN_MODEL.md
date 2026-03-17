# Domain Model

## Core modeling language
Use a shared node / edge / state / event model.

## Nodes
- Tenant
- Business
- Location
- Department / Team
- Area / Sector / Zone
- Unit / Room / Site / Asset / Vehicle / Job Site
- User
- Worker Profile
- Role
- Permission
- Schedule
- Shift
- Task
- Checklist
- Inventory Item
- Stock Location
- Vendor
- Conversation / Message Thread
- Notification
- Attachment

## Scope model
Most business records should include:
- `tenant_id`

Most operational records should usually also include:
- `location_id`

## RBAC model
Atomic permissions are granted through roles, and roles are assigned in scope.
A user can hold different roles in different locations.

## State machines
### Shift
draft -> published -> acknowledged -> in_progress -> completed -> approved

### Task
open -> assigned -> in_progress -> blocked -> done -> verified
