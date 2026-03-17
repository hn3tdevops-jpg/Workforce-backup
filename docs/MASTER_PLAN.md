# Workforce — Master Plan

## Platform definition
Workforce is a multi-tenant operations platform with shared workforce, scheduling, time, communication, inventory, task-management, and audit/event primitives, extended by domain-specific modules and rendered through configurable widget workspaces.

## Strategic goal
Build one stable shared backend that can power:
- hospitality / housekeeping
- maintenance
- field service
- restaurant / food service
- property operations
- general service-job workflows

## Foundation principles
1. Build shared primitives before domain-specific workflows.
2. Keep the system recoverable through branch discipline, changelog discipline, and milestone tags.
3. Treat tenant scope and permission scope as first-class.
4. Use events and audit trails for every meaningful operational state change.
5. Build UI as a configurable workspace shell with widgets.

## Initial milestones
### Milestone 1 — Platform core
- auth works
- tenant/business/location model works
- location-scoped RBAC works
- audit logging exists
- event emission exists
- migrations are reversible
- smoke tests pass

### Milestone 2 — Workforce core
- worker profiles
- availability
- schedules
- assignments
- shift lifecycle
- time entries
- approvals

### Milestone 3 — Shared ops core
- tasks
- checklists
- communications
- inventory
- assets
- attachments
- notifications

### Milestone 4 — Widget shell
- workspace shell
- widget registry
- saved layouts
- permission-aware widget visibility
- tenant/location context switching
