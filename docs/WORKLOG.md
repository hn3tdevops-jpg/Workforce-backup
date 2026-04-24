# Worklog

## 2026-04-13
- Added location-aware permission dependency and resolve_location_from_query helper; updated v1 endpoints to accept location_id query param.

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

## 2026-04-20 — Model consolidation
- Created re-export shims for models: access_control, employee, tenant, user_employee_link, user; preserved full implementations as *_local modules.
- Removed transient extend_existing compatibility flags from local and canonical identity models.
- Ran full test suite: 49 passed.
- Committed code changes that prepare for removing duplicates and Alembic migration planning.
- Next: prepare Alembic migration plan and, after verification, remove the *_local modules one-by-one.

## 2026-04-24 — Migration reconciliation and test run
- Removed optional asgi2wsgi from pyproject.toml and regenerated poetry.lock to fix dependency resolution.
- Installed dependencies via Poetry and ran tests locally: 49 passed.
- Created a proper Alembic merge migration (alembic/versions/merge_0002_20260420_proper.py) to unify divergent migration heads.
- Backed up and rebuilt local SQLite DB from migrations; stamped DB at the merge head.
- Reverted intermediate manual merge attempts and restored DB from backup when recovery was safer.
- Committed migration changes locally; push to remote deferred pending branch reconciliation and review.
- Next: reconcile branch with remote, push changes, run CI, and publish a short MIGRATION_PLAN entry in docs.
