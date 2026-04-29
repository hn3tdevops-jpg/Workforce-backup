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
2026-04-24T11:11:05Z - Added master plan draft (docs/plans/MASTER_PLAN_DRAFT.md) on branch master-plan-draft
2026-04-24T11:12:36Z - Opened PR: Warning: 4 uncommitted changes
https://github.com/hn3tdevops-jpg/Workforce-backup/pull/14
2026-04-24T11:15:33Z - Opened PR: Warning: 4 uncommitted changes
https://github.com/hn3tdevops-jpg/Workforce-backup/pull/15

## 2026-04-24 — Style & lint cleanup
- Applied black, isort and autoflake to codebase; committed formatting changes.
- Added .flake8 to suppress select false-positives and used inline noqa where runtime import ordering is required.
- Fixed three remaining lint issues (line-length and unused var) and verified tests pass: 49 passed.
- Pushed changes to origin/main.

## 2026-04-28 — Boot-path recovery and deployment wrapper fix
- Added `SKIP_WORKFORCE_MODELS=1` default in `apps/api/app/main.py` and `wsgi.py` so the app boots against the safe local model path instead of double-registering SQLAlchemy tables.
- Declared the missing `a2wsgi` runtime dependency in `pyproject.toml` and `requirements.txt` so the PythonAnywhere WSGI wrapper can import cleanly.
- Verified direct imports succeed, model registration completes, the deployment wrapper imports once `a2wsgi` is installed, and the full pytest suite passes: 52 passed.
- Next: confirm the live deployment has the updated dependency set and then move to the Phase 0 checkpoint/tag.

## 2026-04-28 — Backend follow-through for permissions and RBAC
- Added `GET /api/v1/me/effective-permissions` to the real runtime route and verified it with `tests/test_me_effective_permissions.py`.
- Strengthened the tenant service last-location-owner guard before location-role removal.
- Verified the core slice passes: 6 tests green.
