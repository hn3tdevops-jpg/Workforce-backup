# Worklog

## 2026-05-05 — Add GET /api/v1/auth/me/access-context endpoint

### Context
The PythonAnywhere production frontend (`Workforce-Showcase`) calls the Python backend
directly at `https://hn3t.pythonanywhere.com/api/v1`. PR #28 fixed the local dev proxy
but not the production backend. This adds the missing Python endpoint.

### Changes
- Added `AccessContextScope` and `AccessContextResponse` Pydantic models to `auth.py`.
- Added `GET /api/v1/auth/me/access-context` that returns a COMPAT scope built from
  the user's current RBAC data (`get_effective_role_names`, `get_effective_permission_codes`).
- A user without an active membership for the token's `business_id` receives
  `has_access=False` with `active_scope_count=0` and an empty `scopes` list.
- 5 tests added in `tests/test_auth_access_context.py`; all 58 tests pass.

- Restored `docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT_2026-05-03.md` (full evaluation of all three repos) from closed PR #22 commit 3b7187bea1599463be1a2c90d671db5e924babe3.
- Added supersession notice to `docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT.md` pointing to the dated report.
- No source code changed.

## 2026-05-03 — Phase 0 blocker resolution (RBAC audit, CORS fix, CI fix)

### RBAC audit findings
- Confirmed canonical runtime RBAC uses `roles / role_permissions / scoped_role_assignments / memberships / permissions` (local models in `access_control_local.py`, created by migration `0003_platform_access_control`).
- The `packages/workforce/workforce/app/models/identity.py` defines `biz_roles / biz_role_permissions / membership_roles / membership_location_roles` — these are the frozen legacy package surface (D-0004) and are NOT created by any canonical migration. They are orphaned in the context of the deployed API.
- The evaluation report's description of "active biz_roles system" was inaccurate — the runtime API always runs with `SKIP_WORKFORCE_MODELS=1` (set in `main.py`) which means the local schema is always used.
- SKIP_WORKFORCE_MODELS is required because `apps/api/app/models/access_control.py` and `packages/workforce/workforce/app/models/identity.py` both define a `memberships` table via different SQLAlchemy `Base` metadata, causing double-registration on import. It must stay until the packages/workforce surface is archived.
- Documented canonical RBAC decision as D-0011 in DECISIONS.md.

### CORS fix
- Added `https://hospitable-web.onrender.com` to the CORS allowlist in `apps/api/app/main.py`.
  - Rationale: the Render service is named `hospitable-web` in `render.yaml`; its public URL is `https://hospitable-web.onrender.com`. This origin was missing from the allowlist.
  - The `CORS_ALLOW_ORIGINS` environment variable override remains available for production configuration if the domain changes.
  - `allow_credentials=False` is correct and intentional: the API uses Bearer tokens in the Authorization header, not cookies. Credentials mode is not required.

### Import root findings
- `apps/api/app/` contains 75 `from apps.api.app.*` imports and 24 `from app.*` imports.
- Both roots resolve to the same package because `pyproject.toml` includes `{ include = "app", from = "apps/api" }` and `PYTHONPATH=apps/api` is set at runtime.
- The canonical root per D-0006 is `app` (i.e., `PYTHONPATH=apps/api`). Files using `apps.api.app.*` are divergent — acceptable now but should be normalized in a follow-up.

### CI fix
- Fixed `.github/workflows/ci.yml`: matrix defined `['3.12','3.13']` but setup step hardcoded `3.13`; fixed to `${{ matrix.python-version }}`. Added `PYTHONPATH: apps/api` and `SKIP_WORKFORCE_MODELS: "1"` env vars. Fixed test command to `pytest -q tests`.
- Added `.github/workflows/backend-ci.yml`: minimal, focused workflow that installs deps, runs `alembic upgrade head` on SQLite, runs `alembic check`, then runs `pytest -q tests`.

### Migration status
- `alembic heads` shows a single head: `20260425_add_membership_fields` — migration graph is linear.
- `alembic current` on a fresh DB returns nothing (DB not stamped); `alembic check` reports not up-to-date.
- PostgreSQL migration verification is not possible in this environment (no PostgreSQL available locally).
- Follow-up task created: see TODO.md — "Verify Alembic migration chain on PostgreSQL before cutting foundation-v0.1 tag".

### Tests
- 53 tests passed: `PYTHONPATH=apps/api SKIP_WORKFORCE_MODELS=1 python -m pytest -q tests`


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

## 2026-05-03 — Cross-repo evaluation report
- Created `docs/reports/` directory and `docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT.md`.
- workforce-showcase and workforce-console returned 404 from GitHub API; placeholder sections created for both.
- Key findings: dual RBAC schema, CORS mismatch (render.yaml API URL not in CORS allowlist), no CI/CD, no individual REPO_EVALUATION_REPORT.md files exist yet.
- Next: create individual REPO_EVALUATION_REPORT.md for workforce-backup; gain access to showcase and console repos.

## 2026-04-28 — Backend follow-through for permissions and RBAC
- Added `GET /api/v1/me/effective-permissions` to the real runtime route and verified it with `tests/test_me_effective_permissions.py`.
- Strengthened the tenant service last-location-owner guard before location-role removal.
- Verified the core slice passes: 6 tests green.
