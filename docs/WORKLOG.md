# Worklog

## 2026-03-16
- Created repo-base scaffold for Workforce.
- Added planning, control, Copilot, and recovery files.
- Set initial implementation order around foundation freeze, tenancy, RBAC, audit/events, shared ops, and widget shell.

## 2026-03-16 — Canonical backend surface passes
- Fixed canonical backend imports to use `app.*`
- Fixed router wiring for v1 endpoints
- Removed silent router registration drift
- Corrected test import path in `tests/conftest.py`
- Confirmed canonical route inventory includes health, rooms, tasks, assignments, shifts, and bootstrap
- Verified canonical test suite passes: 11 passed

## 2026-03-16 — Normalized model registration and settings base
- Updated canonical model registration to use `app.*` imports
- Separated core model imports from domain model imports
- Updated default database URL to async-compatible sqlite driver
- Added cached settings loader
- Confirmed next implementation target is Phase 1 tenancy and RBAC

## 2026-03-18 — Fixed SQLite migration strategy for platform access control
- `0003_platform_access_control` failed on SQLite because foreign key constraint creation on an existing table required batch mode
- Updated the migration to use `batch_alter_table` for `businesses.tenant_id`
- Rebuilt local dev DB from migrations after partial non-transactional DDL failure
- Preserved stable backend/test checkpoint while continuing schema expansion
