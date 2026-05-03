# Changelog

## 2026-05-03
### Added
- `docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT_2026-05-03.md` — full cross-repo evaluation covering all three repos: workforce-backup (main), Workforce-Showcase (master), Workforce-Console (docs/reconcile-backend-roots). Supersedes placeholder sections in the prior report.
  - Exact backend route inventory and schema shapes
  - Frontend/backend contract matrix with exact mismatches
  - CORS/domain matrix (Showcase CORS now confirmed compatible)
  - RBAC dual-layer assessment (session vs employment scope)
  - CI status (Showcase CI broken: stale poetry.lock; backend 53/53 passing)
  - `/auth/me/access-context` gap identified (only in local Node.js proxy, not Python backend)
  - Phase 0 tag assessment and prioritized fix list
- `docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT.md` — updated with supersession notice pointing to the dated report above.
- `docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT.md` — cross-repo evaluation covering workforce-backup, with placeholder sections for workforce-showcase and workforce-console (both inaccessible at time of writing).
- `docs/DECISIONS.md` D-0011 — canonical RBAC model decision: `roles / role_permissions / scoped_role_assignments` are the authoritative tables; `biz_roles / biz_role_permissions / membership_roles / membership_location_roles` are legacy/orphaned and not used by the runtime API.
- `.github/workflows/backend-ci.yml` — minimal CI workflow: installs dependencies, runs `alembic upgrade head`, runs `pytest -q tests` with `PYTHONPATH=apps/api` and `SKIP_WORKFORCE_MODELS=1`.

### Fixed
- `.github/workflows/ci.yml` — corrected Python version matrix vs setup-python mismatch (was hardcoding `3.13` regardless of matrix value); added `PYTHONPATH=apps/api` and `SKIP_WORKFORCE_MODELS=1` env vars; fixed test command to `pytest -q tests`.
- `apps/api/app/main.py` CORS allowlist — added `https://hospitable-web.onrender.com` (the Render-deployed frontend origin per `render.yaml` service name). Documented that `allow_credentials=False` is intentional: the API uses Bearer token auth (Authorization header), not cookies, so credentials mode is not required.

## 2026-04-27
### Added
- Centralized import guard and diagnostics to stabilize tests (SKIP_WORKFORCE_MODELS).
- Admin invite endpoint and admin-create-with-membership seeding: creates Memberships (invited/active) and owner role assignment when requested.

### Fixed
- Clarified behavior: public /auth/register creates a user account but does not create a workspace/membership; admin invite/create flows seed memberships.

### Details
- Database tables and key columns touched/created by the flows:
  - users: id, email, hashed_password, is_active, business_id
  - businesses: id, tenant_id, name
  - memberships: id, user_id, business_id, status, is_owner
  - scoped_role_assignments: id, membership_id, role_id, location_id
  - roles: id, business_id, name (seeded by async_seed_default_roles_for_business)
  - membership_roles (optional): membership_id, role_id

- Endpoints responsible for creation and their behaviour:
  - POST /api/v1/users/invite?business_id={business.id}
    - Creates a stub User (is_active=false) when missing and a Membership with status='invited'.
    - Example request (curl):
      curl -X POST "http://localhost:8000/api/v1/users/invite?business_id=<BUSINESS_ID>" \
        -H "Content-Type: application/json" \
        -d '{"email":"invitee@example.com","role_ids": []}'
    - Successful response (201): {"membership_id":"<id>", "user_id":"<id>", "email":"invitee@example.com"}

  - POST /api/v1/users/ with JSON including business_id and is_owner
    - Creates User record and, when business_id supplied, creates an active Membership (status='active'), seeds default roles for that business and optionally assigns the Owner ScopedRoleAssignment.
    - Example request (curl):
      curl -X POST "http://localhost:8000/api/v1/users/" \
        -H "Content-Type: application/json" \
        -d '{"email":"user@example.com","business_id":"<BUSINESS_ID>","is_owner":true}'
    - Successful response (201): includes user fields and memberships list, e.g. {"id":"...","email":"user@example.com", "memberships":[{"business_id":"<BUSINESS_ID>","status":"active","is_owner":true}]}

- Behaviour preserved for public registration and login:
  - POST /api/v1/auth/register creates an account but does NOT create any Business or Membership.
  - POST /api/v1/auth/login continues to require an active Membership. A newly registered user without an active membership receives 403: {"detail":"User has no active memberships."}
  - This rule is intentionally preserved: login must not create memberships as a side-effect.

- Commands used during investigation and verification:
  - pytest -q (ran full test suite; 52 passed locally)
  - pytest -q tests/test_users_endpoints.py::test_invite_user_creates_invited_membership
  - git add -A && git commit -m "...Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
  - git push -u origin fix/guard-workforce-models-for-tests
  - gh pr create / gh pr comment to open PR #18

- Test results summary:
  - Full local test run: 52 passed in ~10s
  - New tests added: tests/test_users_endpoints.py::test_create_user_with_membership and tests/test_users_endpoints.py::test_invite_user_creates_invited_membership

## 2026-04-24
### Fixed
- Applied code formatting and import sorting (black, isort) and removed unused imports (autoflake). Updated .flake8 to reduce false-positives; fixed small test issues and import placement.
- Ran full test suite: 49 passed.

## 2026-04-13
### Changed
- Permission dependencies now support optional location-scoped checks. Endpoints accept optional `location_id` query param which is forwarded to permission resolver.

## 2026-03-16
### Added
- repo operating system docs
- Copilot repo instructions
- backend and frontend instruction files
- PR template
- recovery playbook
- domain model and architecture docs
- checkpoint helper script
