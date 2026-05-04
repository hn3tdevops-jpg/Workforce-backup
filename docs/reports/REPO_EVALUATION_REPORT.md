# Repo Evaluation Report: Workforce-backup

**Generated:** 2026-05-04  
**Analyst:** GitHub Copilot automated evaluation  
**Repository:** hn3tdevops-jpg/Workforce-backup  
**Related repos inspected:** hn3tdevops-jpg/Workforce-Showcase, hn3tdevops-jpg/Workforce-Console (cross-repo detail in `WORKFORCE_CROSS_REPO_EVALUATION_REPORT_2026-05-03.md`)

---

## 1. Executive Summary

### Purpose
Workforce-backup is the **canonical backend source-of-truth** for the Workforce multi-tenant service-operations platform. It hosts a FastAPI/SQLAlchemy Python API deployed to PythonAnywhere and also contains an embedded Next.js frontend (`apps/web/hospitable-web`). The repo is **mixed-purpose**: backend API (primary) + embedded frontend (secondary, not the primary frontend).

### Overall Health: 🟡 Foundation Stabilized — Not Yet Production-Ready

The repository is structurally sound and in active development. The canonical API is tested (53/53 passing), the Alembic migration chain is linear and runs cleanly on SQLite, and the RBAC model is documented and actively used. However, the project is self-declared to be in **Phase 0 — Foundation Freeze** with several Phase 0 exit criteria still unmet.

### Production Readiness: **Partially Ready**

| Area | Status | Notes |
|---|---|---|
| Backend API tests | ✅ 53/53 passing | Verified in this evaluation |
| Migration chain (SQLite) | ✅ Clean single head | `20260425_add_membership_fields` |
| Migration chain (PostgreSQL) | ⚠️ Unverified | No PostgreSQL available in CI or locally; TODO item open |
| `SECRET_KEY` env var | ⚠️ Missing in tests | Runtime warning in every test run; not set via env in test context |
| `foundation-v0.1` tag | ❌ Not created | Documented as Phase 0 exit criterion; not yet done |
| Dev DB backup files tracked in git | ❌ D-0005 violation | Multiple `.bak` and `dev.db*.bak` files committed |
| `response.json` tracked in git | ❌ D-0005 violation | Raw API response artifact committed |
| Embedded Next.js CORS | ❌ Mismatch | `render.yaml` targets `api-hn3t.pythonanywhere.com` — NOT in CORS allowlist |
| `GET /auth/me/access-context` | ❌ Not implemented | Required by Showcase frontend; employment-scope permissions silently fail in production |
| Legacy `packages/workforce` models | ⚠️ Still present | `SKIP_WORKFORCE_MODELS=1` guard required at boot/test to prevent double registration |
| `startup.sh` seed script | ⚠️ Domain-specific | References `silver_sands_seed_prod`; not portable across tenants |
| CI (backend-ci.yml) | ✅ Active | Correct PYTHONPATH + SKIP_WORKFORCE_MODELS; runs migrations + tests |
| CI (ci.yml) | ⚠️ Redundant | Kept "for reference" but still triggers on push/PR; no Alembic step; confusing |

### Biggest Risks

1. **SQLite-only migration verification**: The migration chain has never been run on PostgreSQL, which is the target production DB shape. Silent failures or incompatibilities would surface at deployment time.
2. **Dev artifacts tracked in git** (`dev.db.*.bak`, `response.json`, `pyproject.toml.bak`, `index.html.bak`): This violates D-0005, pollutes history, and risks leaking local state.
3. **Missing `GET /auth/me/access-context` endpoint**: The primary frontend (Workforce-Showcase) calls this on startup. Without it, employment-scope permissions (`hasEmployeePermission()`) are always `false` in production.
4. **`SKIP_WORKFORCE_MODELS` boot guard is permanently required**: The legacy `packages/workforce` models are still present and overlap with canonical models. Until this path is formally archived (D-0004), any boot without the guard will cause double SQLAlchemy Table registration.
5. **Embedded Next.js CORS mismatch**: `render.yaml` configures the embedded Next.js frontend to use `https://api-hn3t.pythonanywhere.com` as the API base — a domain NOT in the CORS allowlist. This deployment configuration would fail if the embedded frontend were deployed via Render.

### Highest-Priority Next Actions

1. Remove or `.gitignore` committed dev artifacts (`dev.db.*.bak`, `response.json`, `pyproject.toml.bak`, `index.html.bak`) — Phase 0 hygiene.
2. Verify Alembic migration chain on PostgreSQL before cutting the `foundation-v0.1` tag (open TODO item).
3. Create the `foundation-v0.1` tag — required Phase 0 exit criterion.
4. Implement `GET /api/v1/auth/me/access-context` on the Python backend (or document explicitly that it will not be implemented and update the Showcase frontend accordingly).
5. Retire or deactivate the legacy `ci.yml` so it does not run alongside `backend-ci.yml`.
6. Document or remove the `startup.sh` Silver Sands seed reference — it is domain-specific and not portable.

### Repo Classification
**Mixed-purpose**: Primary backend API with embedded secondary frontend (Next.js). Not a showcase/demo repo. Not a docs-only or deployment-only repo.

---

## 2. Repository Identity

### Shell outputs

```
pwd:
/home/runner/work/Workforce-backup/Workforce-backup

git status --short:
(no uncommitted changes on evaluation branch)

git branch --show-current:
copilot/create-repo-evaluation-report

git remote -v:
origin  https://github.com/hn3tdevops-jpg/Workforce-backup (fetch)
origin  https://github.com/hn3tdevops-jpg/Workforce-backup (push)

git log -1 --oneline:
3368051 Merge pull request #24 from hn3tdevops-jpg/copilot/restore-evaluation-report-from-pr-22
```

### Key files found

```
./AGENTS.md
./PHASE1-TENANCY-CHECKLIST.md
./README.md
./README_APPLY_FIRST.md
./SILVER_SANDS_INTEGRATION_PLAN.md
./alembic.ini
./docker-compose.yml
./pyproject.toml
./render.yaml
./requirements.txt
./apps/api/README.md
./apps/web/hospitable-web/Dockerfile
./apps/web/hospitable-web/package.json
./apps/web/hospitable-web/pnpm-lock.yaml
./apps/web/hospitable-web/pnpm-workspace.yaml
./apps/web/hospitable-web/tsconfig.json
./docs/ARCHITECTURE.md
./docs/CHANGELOG.md
./docs/DECISIONS.md
./docs/DOMAIN_MODEL.md
./docs/MASTER_PLAN.md
./docs/MIGRATION_PLAN.md
./docs/MODULE_CATALOG.md
./docs/PHASE_STATUS.md
./docs/ROADMAP.md
./docs/TODO.md
./docs/WORKLOG.md
./docs/architecture/REPO_STRUCTURE.md
./docs/rbac/RBAC_IMPLEMENTATION_AUDIT.md
./docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT_2026-05-03.md
```

### Languages
- **Primary**: Python 3.12 (backend API)
- **Secondary**: TypeScript / React (embedded Next.js frontend `apps/web/hospitable-web`)

### Frameworks and Libraries

| Layer | Library | Version (pyproject.toml) |
|---|---|---|
| API | FastAPI | >=0.111.0 |
| ASGI server | Uvicorn (standard) | >=0.29.0 |
| ORM | SQLAlchemy (asyncio) | >=2.0.0 |
| Migrations | Alembic | >=1.13.0 |
| Schemas | Pydantic v2 | >=2.0.0 |
| Settings | pydantic-settings | >=2.0.0 |
| Auth tokens | python-jose (cryptography) | >=3.3.0 |
| Password hashing | passlib (bcrypt) | >=1.7.4 |
| Async DB (test/dev) | aiosqlite | >=0.20.0 |
| Async DB (prod) | asyncpg | >=0.29.0 |
| WSGI adapter | a2wsgi | >=1.10.10 |
| HTTP client (test) | httpx | >=0.27.0 |
| Frontend framework | Next.js | 14.x |
| Frontend runtime | React | ^18.0.0 |

### Package Manager and Build System
- **Backend**: Poetry (`pyproject.toml` + `poetry.lock`)
- **Frontend (embedded)**: pnpm 9.15.4 (`apps/web/hospitable-web/pnpm-workspace.yaml`)

### Runtime and Deployment Model

| Target | Details |
|---|---|
| **Backend production** | PythonAnywhere (`hn3t.pythonanywhere.com`), WSGI via `a2wsgi` adapter (`wsgi.py`) |
| **Backend ASGI entrypoint** | `apps.api.app.main:app` (FastAPI) |
| **Backend WSGI entrypoint** | `wsgi.py` → `ASGIMiddleware(asgi_app)` |
| **Frontend production** | Render (Node.js service) via `render.yaml`; `pnpm build` + `pnpm start` |
| **Dev server** | Uvicorn (`uvicorn apps.api.app.main:app --host 0.0.0.0 --port 8000`) |
| **Database (prod)** | PostgreSQL 15 (per `docker-compose.yml`, asyncpg driver) |
| **Database (dev/test/CI)** | SQLite (`aiosqlite`) |
| **Startup script** | `startup.sh` (runs migrations, domain seed, uvicorn) |

### Primary Entrypoints

| Purpose | Path |
|---|---|
| FastAPI app | `apps/api/app/main.py` |
| WSGI wrapper (PythonAnywhere) | `wsgi.py` |
| API router | `apps/api/app/api/router.py` |
| Startup (Uvicorn/seed) | `startup.sh` |
| Next.js dev server | `apps/web/hospitable-web/package.json` → `pnpm dev` |
| Backend test suite | `tests/` (from repo root, `PYTHONPATH=apps/api SKIP_WORKFORCE_MODELS=1`) |

### Main Config Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Poetry backend deps, Python 3.12, pytest config |
| `alembic.ini` | Alembic migration config |
| `render.yaml` | Render deployment (Node.js frontend service) |
| `docker-compose.yml` | Local PostgreSQL dev DB; web service commented out |
| `apps/web/hospitable-web/package.json` | Next.js frontend deps |
| `apps/web/hospitable-web/tsconfig.json` | TypeScript config |
| `.flake8` | Flake8 lint config |
| `pytest.ini` | Pytest settings (asyncio_mode = auto) |
| `.github/workflows/backend-ci.yml` | Primary CI workflow |
| `.github/workflows/ci.yml` | Legacy CI workflow (superseded but still active) |
| `apps/api/app/core/config.py` | Pydantic settings (DATABASE_URL, SECRET_KEY, etc.) |

### Documentation and Source-of-Truth Files

| File | Purpose |
|---|---|
| `docs/DECISIONS.md` | Architectural decision records (D-0001 through D-0011 + migrations) |
| `docs/ROADMAP.md` | Phase roadmap (Phase 0–6) |
| `docs/PHASE_STATUS.md` | Current phase status and exit criteria |
| `docs/TODO.md` | Current and next phase task list |
| `docs/WORKLOG.md` | Chronological change log with commands run |
| `docs/CHANGELOG.md` | Structured changelog by date |
| `docs/ARCHITECTURE.md` | Architecture overview and layer guidance |
| `docs/DOMAIN_MODEL.md` | Core modeling language, nodes, scope model, state machines |
| `docs/MODULE_CATALOG.md` | Shared platform and domain module catalog |
| `docs/rbac/RBAC_IMPLEMENTATION_AUDIT.md` | RBAC audit index |
| `docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT_2026-05-03.md` | Cross-repo evaluation (all three Workforce repos) |
| `AGENTS.md` | Copilot/agent operating rules |
| `.github/copilot-instructions.md` | Copilot coding instructions |

---

## 3. Backend API Inventory

**Source:** `apps/api/app/api/router.py`, `apps/api/app/api/v1/endpoints/`

| Route | Method(s) | Auth Required | Notes |
|---|---|---|---|
| `/` | GET | No | `{"message": "Workforce API is running"}` |
| `/health` | GET | No | `{"status": "ok"}` (plain; not prefixed with `/api/v1`) |
| `/api/v1/health` | GET | No | Versioned health check |
| `/api/v1/auth/login` | POST | No | Returns `{access_token, token_type, business_id, user{id,email,is_active}}`; 403 if no active membership |
| `/api/v1/auth/register` | POST | No | Creates user only — no membership, no business |
| `/api/v1/auth/me` | GET | Yes | Returns `{user, business_id, memberships, roles, permissions}` |
| `/api/v1/auth/switch-business` | POST | Yes | Returns `{access_token, token_type, business_id, roles, permissions}` |
| `/api/v1/bootstrap` | POST | No | One-time server init: creates tenant/business/location/admin |
| `/api/v1/me/businesses` | GET | Yes | Returns `[{id, name, is_default}]` |
| `/api/v1/me/effective-permissions` | GET | Yes | Returns sorted `string[]` of permission codes |
| `/api/v1/rooms` | GET/POST/etc. | Yes | Room management |
| `/api/v1/users` | GET/POST/etc. | Yes | User management; includes invite endpoint |
| `/api/v1/employees` | GET/POST/etc. | Yes | Employee profile management |
| `/api/v1/tasks` | GET/POST/etc. | Yes | Task management |
| `/api/v1/assignments` | GET/POST/etc. | Yes | Assignment management |
| `/api/v1/shifts` | GET/POST/etc. | Yes | Shift management |

**Endpoint NOT implemented (gap identified in cross-repo evaluation):**
- `GET /api/v1/auth/me/access-context` — required by the Workforce-Showcase frontend at startup for employment-scope permissions; only implemented in the Showcase local Node.js proxy.

---

## 4. Data Model and Migration State

### Canonical models (`apps/api/app/models/`)

| Module | Models |
|---|---|
| `access_control_local.py` (canonical) | `Membership`, `Role`, `Permission`, `RolePermission`, `ScopedRoleAssignment` |
| `tenant_local.py` | `Tenant`, `Business`, `Location` |
| `user_local.py` | `User` |
| `employee_local.py` | `Employee` |
| `user_employee_link_local.py` | `UserEmployeeLink` |

**Note:** `*_local.py` files are the active implementations. Each `*.py` (non-`_local`) is a re-export shim that conditionally imports from the legacy `packages/workforce` path when `SKIP_WORKFORCE_MODELS` is not set. When the env var is set (as in all tests, CI, and boot paths), the `_local` implementations are used exclusively.

### Alembic migration chain (root `alembic/`)

| Migration ID | Description |
|---|---|
| `0001_initial` | Initial schema (users, businesses, etc.) |
| `0002_hospitable_property_ops` | Property operations (rooms, tasks, assignments, shifts) |
| `0003_platform_access_control` | Platform RBAC: memberships, roles, permissions, scoped_role_assignments |
| `0001_create_employee_and_user_employee_link_tables` | Employee and user-employee link tables |
| `0002_normalize_uuid_columns` | UUID column normalization |
| `20260420_consolidate_models` | Model consolidation |
| `merge_0002_20260420_proper` | Merge revision (unifies 2 divergent heads) |
| `20260425_add_user_profile_fields` | User profile fields (first_name, last_name, phone) |
| `20260425_add_membership_fields` | **HEAD** — primary_location_id, updated_at on memberships |

**Migration chain status:** Single head. Runs cleanly on SQLite (verified in this evaluation). **PostgreSQL not verified** (open TODO item; no PG instance available in CI or evaluation env).

### Alembic dead ends / legacy surfaces

- `apps/ops/hospitable-ops/alembic.ini` — separate Alembic config for a domain ops module; not part of the canonical chain.
- `packages/workforce/workforce/alembic.ini` — legacy package migrations; not in the canonical chain (D-0004: frozen surface).

---

## 5. RBAC and Tenant Safety

### RBAC model (D-0011)

The canonical runtime RBAC uses five tables:

| Table | Role |
|---|---|
| `memberships` | Links User to Business; carries `status` and `primary_location_id` |
| `roles` | Role definitions per business |
| `permissions` | Atomic permission codes (e.g. `schedule:read`, `hk.tasks.manage`) |
| `role_permissions` | Many-to-many: role → permission |
| `scoped_role_assignments` | Binds a Membership to a Role, optionally scoped to a Location |

**Permission resolution path:** `User` → `Membership` → `ScopedRoleAssignment` → `Role` → `RolePermission` → `Permission.code`

**Location scoping:** `ScopedRoleAssignment.location_id = NULL` means business-wide; a non-null value restricts the role to a specific location. Permission resolution correctly ORs business-wide and location-scoped assignments.

**Legacy tables (NOT used by runtime API):** `biz_roles`, `biz_role_permissions`, `membership_roles`, `membership_location_roles` — these exist in `packages/workforce/workforce/app/models/identity.py` only. No canonical migration creates them. Not accessed by any route handler or service.

### Tenant and location scoping

- `businesses` carry `tenant_id` (verified in `0003_platform_access_control` migration).
- `memberships` carry `business_id` and `primary_location_id`.
- Route protection tests (`test_route_protection_*.py`) confirm that permission checks are enforced at route level.
- Location-scope behavior tested in `test_location_scope_behavior.py` and `test_permission_location_scope.py`.

### Auth model

- Bearer token (`Authorization: Bearer <token>`) via `python-jose` JWT.
- `allow_credentials=False` on CORS — compatible with header-based auth (no cookies).
- `SECRET_KEY` must be set via environment variable in production; tests issue `RuntimeWarning` because it falls back to an insecure default.

---

## 6. Frontend Analysis (Embedded Next.js)

**Location:** `apps/web/hospitable-web/`  
**Framework:** Next.js 14.x, React 18, TypeScript  
**Package manager:** pnpm 9.15.4  
**Deploy target:** Render (Node.js service, per `render.yaml`)

### CORS issue
`render.yaml` sets `NEXT_PUBLIC_API_BASE_URL=https://api-hn3t.pythonanywhere.com`. This domain (`api-hn3t.pythonanywhere.com`) is **not** in the backend CORS allowlist. If this Next.js app were deployed to Render and made API calls, every request would receive a CORS error. This is a confirmed bug in the deployment configuration.

### Pages and modules

The embedded frontend covers:
- `app/rooms/` — Room management board
- `app/housekeeping/` — Housekeeping tasks
- `app/assignments/` — Staff assignments
- `app/shifts/` — Shift scheduling
- `app/settings/` — Settings shell
- `app/maintenance/`, `app/inventory/`, `app/property-setup/` — Additional modules
- `app/inspections/` — Inspection module

### Relationship to primary frontend
The primary production frontend is in the **Workforce-Showcase** repo (`artifacts/workforce-console` — a Vite/React SPA), not this embedded Next.js app. The embedded Next.js frontend appears to be a parallel development effort. Its deployment status and relationship to the Showcase frontend is not fully documented within this repo. The two frontends have divergent API client implementations (this one targets `api-hn3t.pythonanywhere.com`; Showcase targets `hn3t.pythonanywhere.com`).

---

## 7. Test Suite

**Test runner:** pytest (async via `pytest-asyncio`)  
**Test root:** `tests/` (from repo root)  
**Required env:** `PYTHONPATH=apps/api SKIP_WORKFORCE_MODELS=1`  
**Verified result (this evaluation):** **53 passed, 44 warnings** in ~7.8s

### Test files

| File | Lines | Coverage area |
|---|---|---|
| `test_health.py` | 8 | Health endpoint |
| `test_cors.py` | 44 | CORS middleware |
| `test_auth_endpoints.py` | 390 | Login, register, me, switch-business |
| `test_bootstrap.py` | 125 | Bootstrap initialization |
| `test_rbac_service.py` | 222 | RBAC service logic |
| `test_rbac_seed_service.py` | 92 | Role seeding |
| `test_me_businesses.py` | 36 | `/me/businesses` endpoint |
| `test_me_effective_permissions.py` | 24 | `/me/effective-permissions` |
| `test_permission_location_scope.py` | 49 | Location-scoped permissions |
| `test_location_scope_behavior.py` | 129 | Location scope behavior |
| `test_route_protection_rooms.py` | 120 | Route auth guard (rooms) |
| `test_route_protection_tasks.py` | 120 | Route auth guard (tasks) |
| `test_route_protection_assignments.py` | 124 | Route auth guard (assignments) |
| `test_route_protection_shifts.py` | 122 | Route auth guard (shifts) |
| `test_users_endpoints.py` | 103 | User creation, invite |
| `test_employee_link.py` | 139 | User-employee link |
| `test_api_phase3.py` | 36 | Phase 3 API smoke tests |
| `conftest.py` | 279 | Shared fixtures and DB setup |

### Notable gaps in test coverage

- No tests for `GET /api/v1/auth/me/access-context` (endpoint does not exist)
- No acceptance/integration tests against PostgreSQL
- No tests for `startup.sh` seed behavior
- No frontend tests (embedded Next.js has a Jest config but no apparent test files in this directory)
- No tests for multi-tenant isolation (cross-tenant data leakage scenarios)

### Known warnings

All 44 warnings are `RuntimeWarning: SECRET_KEY is not configured` — emitted during JWT token creation in route protection tests. Not a functional failure but should be resolved by setting `SECRET_KEY` in the test fixture or `conftest.py`.

---

## 8. CI / CD

### `.github/workflows/backend-ci.yml` (primary, active)

- Triggers: push/PR to `main` or `master`
- Python: 3.12
- Env: `PYTHONPATH=apps/api`, `SKIP_WORKFORCE_MODELS=1`, `DATABASE_URL=sqlite+aiosqlite:///./workforce_ci.db`
- Steps: checkout → setup-python → install Poetry → `alembic upgrade head` → `pytest -q tests`
- **Status: Active and correct**

### `.github/workflows/ci.yml` (legacy, still active)

- Triggers: push/PR to `main` or `master`
- Python matrix: 3.12 and 3.13
- Env: `PYTHONPATH=apps/api`, `SKIP_WORKFORCE_MODELS=1`
- Runs `pytest -q tests` **without** running Alembic migrations first
- Header note says "superseded by backend-ci.yml" but the workflow is still active and will run concurrently on every push
- **Status: Redundant; should be disabled or deleted**

### `.github/workflows/acceptance-tests.yml`

- Purpose not inspected in detail; likely integration/acceptance tests
- Status: **Cannot be confirmed without inspecting workflow file contents**

### `.github/workflows/copilot-setup-steps.yml`

- Copilot agent environment setup steps
- Not a CI validation workflow

### No CD pipeline

- There is no CI/CD pipeline that deploys to PythonAnywhere. Deployment appears to be manual.
- `render.yaml` describes a Render service for the embedded Next.js frontend, but there is no GitHub Actions workflow that triggers a Render deploy.

---

## 9. Known Tracked Artifacts (D-0005 Violations)

The following files are committed to the repository and should be removed (or `.gitignore`-'d if regenerated):

| File | Type | Issue |
|---|---|---|
| `dev.db.before-add-updated-at-20260424T153519Z.bak` | Dev DB backup | D-0005: local-only artifact |
| `dev.db.rebuild.bak` | Dev DB backup | D-0005: local-only artifact |
| `index.html.bak` | HTML backup | D-0005: local-only artifact |
| `pyproject.toml.bak` | Config backup | D-0005: local-only artifact |
| `packages/workforce/workforce/app/models/identity.py.before-location-runtime-import-20260424T153013Z.bak` | Python file backup | D-0005: local-only artifact |
| `packages/workforce/workforce/app/templates/index.html.bak` | Template backup | D-0005: local-only artifact |
| `response.json` | Raw API response | D-0005: local-only artifact |

Note: The `.gitignore` already excludes `*.db`, `*.db.bak*`, and `dev.db.pre_*.bak` patterns — but the above files were committed before these rules were in place (or use slightly different naming).

---

## 10. Packages / Legacy Surfaces

### `packages/workforce/workforce/`
- **Status:** Frozen legacy surface (D-0004)
- Contains: `app/models/identity.py` (has `User`, `Business`, `Location`, and legacy RBAC tables `biz_roles`, etc.)
- **Not used by runtime API** when `SKIP_WORKFORCE_MODELS=1` is set
- `SKIP_WORKFORCE_MODELS=1` must remain set until this is formally archived
- Has its own `alembic.ini` and `pyproject.toml` — not part of canonical migration chain

### `packages/hospitable/hospitable/`
- Hospitality-specific domain models
- **Status:** Frozen legacy surface (D-0004)

### `packages/contracts/` and `packages/domain/`
- Shared library space
- README files present but limited implementation visible

### `apps/ops/hospitable-ops/`
- Domain-specific operational module with its own `alembic.ini`
- Not part of canonical API surface

---

## 11. Open Issues and Prioritized Actions

### Critical (block production safety or Phase 0 completion)

| Priority | Issue | Source |
|---|---|---|
| P1 | Verify Alembic migration chain on PostgreSQL | TODO.md, WORKLOG.md |
| P1 | Create `foundation-v0.1` tag | TODO.md, PHASE_STATUS.md |
| P1 | Remove or `.gitignore` dev artifacts committed in violation of D-0005 | D-0005, git ls-files |
| P1 | Set `SECRET_KEY` in test fixture (`conftest.py`) to eliminate 44 test warnings | Tests |

### High (functional gaps or production correctness)

| Priority | Issue | Source |
|---|---|---|
| P2 | Implement `GET /api/v1/auth/me/access-context` or formally document that employment-scope permissions are deferred | Cross-repo eval, CHANGELOG |
| P2 | Fix `render.yaml` — change `NEXT_PUBLIC_API_BASE_URL` to `https://hn3t.pythonanywhere.com` or add `api-hn3t.pythonanywhere.com` to CORS allowlist | render.yaml, main.py |
| P2 | Disable or delete `.github/workflows/ci.yml` (superseded, still runs concurrently) | ci.yml header comment |
| P2 | Document or remove the Silver Sands domain-specific seed step in `startup.sh` | startup.sh |

### Medium (tech debt / Phase 1 readiness)

| Priority | Issue | Source |
|---|---|---|
| P3 | Archive `packages/workforce` surface and remove `SKIP_WORKFORCE_MODELS` guard (D-0004 follow-up) | DECISIONS.md D-0011 |
| P3 | Remove `*_local` shim pattern once packages/workforce is archived | models/ directory |
| P3 | Add audit log and domain event tables (Phase 2 prerequisite) | ROADMAP.md |
| P3 | Define explicit permission catalog — current codes are scattered in tests, not centralized | MODULE_CATALOG.md, tests |
| P3 | Validate that multi-tenant isolation tests exist (cross-tenant data leakage) | Test review |

---

## 12. Dependency on Other Workforce Repos

This repo is **partially dependent** on the other Workforce repos in the following ways:

| Dependency | Repo | Nature | Risk |
|---|---|---|---|
| `GET /auth/me/access-context` endpoint | Workforce-Showcase (`artifacts/workforce-console/src/lib/auth-context.tsx`) | Frontend calls endpoint not implemented in this backend | Medium — employment-scope permissions are silently broken in production |
| OpenAPI spec divergence | Workforce-Showcase (`lib/api-spec/openapi.yaml`) | Spec describes `SessionInfo` shape that diverges from `MeResponse` | Low — frontend uses defensive mapping |
| `bootstrap` endpoint contract | Workforce-Console, Workforce-Showcase | Showcase/Console assumed `GET /bootstrap` returns feature flags; Python backend uses `POST /bootstrap` for one-time init | Medium — confusing; routes should not collide conceptually |
| Frontend CORS domain | Workforce-Showcase | Showcase frontend targets `https://hn3t.pythonanywhere.com` which IS in allowlist | ✅ No blocker |

Full cross-repo analysis: `docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT_2026-05-03.md`

---

## 13. Assumptions and Unverifiable Items

The following could not be verified from this repo alone:

| Item | Reason |
|---|---|
| PostgreSQL migration correctness | No PostgreSQL instance available in evaluation env |
| PythonAnywhere live deployment state | Cannot connect to PythonAnywhere from evaluation env |
| Whether the embedded Next.js frontend (`apps/web/hospitable-web`) is actively deployed or deprecated in favor of Showcase | No explicit deprecation notice; `render.yaml` references it but deployment status is unknown |
| Whether `api-hn3t.pythonanywhere.com` is a real separate backend or the same server as `hn3t.pythonanywhere.com` | Domain not reachable from evaluation env; no documentation explains the distinction |
| The current CI run status (pass/fail) for the PR branch | Not checked against GitHub Actions at time of report generation |
| Whether `apps/ops/hospitable-ops/` is currently in use | No route in the canonical `router.py` includes ops endpoints |

---

*Report created by GitHub Copilot evaluation agent. Evidence sourced exclusively from repository files, shell outputs, and test runs within this evaluation session.*
