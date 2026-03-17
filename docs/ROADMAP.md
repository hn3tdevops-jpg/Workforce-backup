# Roadmap

## Phase 0 — Foundation freeze
Goal: stabilize the repo, operating system, and recovery process.

Deliverables:
- project-control docs in place
- Copilot instructions in place
- restore/tag workflow documented
- runtime target documented
- smoke check path documented
- first checkpoint tag created

## Phase 1 — Tenant and RBAC core
Goal: guarantee tenant isolation and scope-aware permissions.

Deliverables:
- tenant/business/location model
- memberships
- roles
- permissions
- scoped user-role assignments
- permission-resolution helpers
- access tests

## Phase 2 — Audit and events
Goal: create a durable change trail and event backbone.

Deliverables:
- audit log table
- domain event table
- event emit helpers
- basic event catalog

## Phase 3 — Workforce/time/scheduling
Goal: build cross-domain labor primitives.

## Phase 4 — Shared operations
Goal: build modules that every service business reuses.

## Phase 5 — Widget workspace shell
Goal: make the UI customizable and role-aware.

## Phase 6 — Domain packs
Goal: deliver industry workflows without corrupting the shared core.
