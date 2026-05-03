# Workforce Cross-Repo Evaluation Report — 2026-05-03 (Updated)

**Generated:** 2026-05-03  
**Previous report:** `docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT.md` (placeholder sections — superseded by this report)  
**Analyst:** GitHub Copilot automated evaluation

---

## Repo Access Summary

| Repo | Branch Inspected | Access | Notes |
|---|---|---|---|
| hn3tdevops-jpg/Workforce-backup | `main` | ✅ Full (cloned locally) | Backend API + embedded Next.js frontend |
| hn3tdevops-jpg/Workforce-Console | `docs/reconcile-backend-roots` | ✅ Full (GitHub API) | Frontend devhub / reconciliation workspace |
| hn3tdevops-jpg/Workforce-Showcase | `master` | ✅ Full (GitHub API) | Primary frontend workspace (SPA + local proxy) |

> All placeholder sections from the previous report are **superseded** by findings below.

---

## 1. Executive Summary

### Overall System Health: 🟡 Foundation Stabilized — Frontend/Backend Contract Partially Aligned

The Workforce platform has progressed since the prior evaluation. The backend is in a stable, tested state (53/53 tests passing). The canonical RBAC model (`roles` / `role_permissions` / `scoped_role_assignments`) is now active in all auth flows. The primary frontend (Workforce-Showcase's `artifacts/workforce-console`) is well-structured, targets the correct production API domain, and uses defensive response mapping that tolerates several backend schema divergences.

**Key findings that supersede the prior report:**
- The CORS mismatch (`api-hn3t.pythonanywhere.com`) was from `render.yaml` targeting the backend's embedded Next.js frontend — not relevant to Showcase. Showcase correctly targets `https://hn3t.pythonanywhere.com` which **is** in the CORS allowlist ✅.
- The dual RBAC concern: the active auth flow now uses the canonical local RBAC tables (`ScopedRoleAssignment`, `Role`, `RolePermission`). The legacy `biz_roles` concern may be partially resolved but should be confirmed via migration inspection.

**Top Blockers (updated):**
1. **`/auth/me/access-context` endpoint gap** — The Showcase frontend calls `GET /api/v1/auth/me/access-context` at startup. This endpoint **does not exist** on the Python backend (`hn3t.pythonanywhere.com`). It is only implemented in the local Node.js `api-server` proxy (Showcase). When running in production without the local proxy, all employment-scope permission checks silently fail (frontend handles the error, sets `employmentScope = null`). This degrades `hasEmployeePermission()` to always return `false`.
2. **`/auth/me` schema drift** — Backend `MeResponse` does not include `first_name`, `last_name`, or `business_name` in memberships. Frontend handles this defensively but the OpenAPI spec in `lib/api-spec/openapi.yaml` describes a `SessionInfo` shape that does not match the actual backend `MeResponse`.
3. **Showcase CI permanently failing** — All 12 CI runs on `main` branch fail with `pyproject.toml changed significantly since poetry.lock was last generated`. Build validation is broken; no CI gate is enforcing correctness.
4. **`POST /api/v1/bootstrap` contract mismatch** — The Showcase/Console's Copilot bootstrap context assumed `GET /bootstrap` returns feature flags. The Python backend's `/api/v1/bootstrap` is a one-time server initialization endpoint (`POST` only, requires empty user table). These are entirely different contracts and should not be conflated.

**Risks resolved since prior report:**
- ✅ CORS origin mismatch resolved — Showcase correctly targets `https://hn3t.pythonanywhere.com`
- ✅ Backend tests pass (53/53 verified)
- ✅ Canonical RBAC active in auth flows
- ✅ Switch-business and login flows are structurally compatible (frontend defensive mapping covers response shape differences)

---

## 2. Repo Profiles

### 2.1 Workforce-backup (main)

| Field | Value |
|---|---|
| Purpose | Backend API source-of-truth. Also contains embedded Next.js frontend (`apps/web/hospitable-web`) |
| Language/Runtime | Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic |
| Package Manager | Poetry (`pyproject.toml` / `poetry.lock`) |
| Entry Point | `apps/api/app/main.py` (FastAPI app) |
| WSGI/Deploy | `wsgi.py` → `a2wsgi` → PythonAnywhere (`hn3t.pythonanywhere.com`) |
| Canonical API Prefix | `/api/v1/` |
| Health Endpoint | `GET /health` → `{"status": "ok"}` |
| CORS Default Origins | `https://hn3t.pythonanywhere.com`, `https://wf-hn3t.pythonanywhere.com`, localhost:5000, localhost:5173, localhost:3000 |
| CORS `allow_credentials` | `False` |
| CI Workflows | `backend-ci.yml` (Backend CI, 2 runs — latest in_progress at eval time) |
| Test Suite | 53 tests, all passing (`PYTHONPATH=apps/api SKIP_WORKFORCE_MODELS=1 python -m pytest -q tests`) |
| Phase Status | Phase 0 Foundation — stable and tested |

**Exact commands run:**
```
cd /home/runner/work/Workforce-backup/Workforce-backup
pip install pytest pytest-asyncio httpx
PYTHONPATH=apps/api SKIP_WORKFORCE_MODELS=1 python -m pytest -q tests
# Result: 53 passed, 44 warnings in 8.26s
```

**Known issues:**
- Dev SQLite backup files (`dev.db.*.bak`) tracked in git root
- `SECRET_KEY` warning in tests (not configured via env var in test context)
- `render.yaml` references `api-hn3t.pythonanywhere.com` as a Next.js frontend env var target — this domain is NOT in the CORS allowlist and that frontend deployment config is inconsistent. However, this does not affect Showcase.

---

### 2.2 Workforce-Showcase (master)

| Field | Value |
|---|---|
| Purpose | Primary frontend workspace: React/Vite SPA (`artifacts/workforce-console`), Node.js local API proxy (`artifacts/api-server`), shared TS libs (`lib/api-client-react`, `lib/api-spec`, `lib/api-zod`, `lib/db`) |
| Package Manager | pnpm (workspace) |
| Build System | Vite (SPA), esbuild (api-server) |
| Frontend App Root | `artifacts/workforce-console/` |
| App Entry Point | `artifacts/workforce-console/src/main.tsx` |
| Deploy Target | PythonAnywhere via `app.py` (Flask SPA server) — serves `dist/` directory |
| VITE_API_BASE_URL (prod) | `https://hn3t.pythonanywhere.com` (in `.env.production`) |
| Vite Dev Proxy Target | `/api/v1/*` → `https://hn3t.pythonanywhere.com` (default, no CORS issue in dev) |
| Production API Fallback | `api-client.ts` hardcodes `https://hn3t.pythonanywhere.com/api/v1` when `VITE_API_BASE_URL` unset |
| CI Workflows | `ci.yml` (CI), `deploy-to-pythonanywhere.yml`, `playwright-ci.yml`, `playwright-browser-validation.yml` |
| CI Status | ❌ All CI runs failing (poetry.lock stale — `pyproject.toml changed significantly`) |
| Demo Mode | `VITE_DEMO_MODE=true` uses hardcoded demo session (`manager@silversands.com`), bypasses all API calls |

**Key frontend structure:**
- `App.tsx`: Routes `/app/*` are protected (require authentication via `AuthProvider`)
- `lib/auth-context.tsx`: `AuthProvider` fetches `GET /auth/me` and `GET /auth/me/access-context` on startup; dual-layer permissions (session + employment scope)
- `lib/api-client.ts`: `fetchApi()` with `Authorization: Bearer` header; no `credentials: 'include'` (compatible with `allow_credentials=False`)
- Pages: Dashboard, Rooms, Tasks, Assignments, Shifts, Users, Studio, Promotions, Employees, Inspections, Maintenance, Inventory, Communications, Settings, BusinessRegister, Invite, ProjectManager (superadmin)

---

### 2.3 Workforce-Console (docs/reconcile-backend-roots)

| Field | Value |
|---|---|
| Purpose | Frontend devhub / reconciliation workspace (Replit-based development context) |
| Structure | `workforce_frontend_app/artifacts/workforce-console/` (one artifact), `workforce_frontend_app/scripts/`, `docs/` |
| Package Manager | pnpm (workspace, `pnpm-workspace.yaml`) |
| CI Workflows | `ci.yml` (Dev Hub CI), `validate-employee-link-editable-install.yml` |
| PROGRESS_REPORT.md | Extensive history — used as Replit workspace for frontend development and backend reconciliation |
| Relationship to Showcase | Contains the same `artifacts/workforce-console` artifact structure; appears to be the editing context that was used to develop what was then published to Workforce-Showcase |

**Assessment:** Workforce-Console is a development/reconciliation workspace, not an independent deployable. The canonical production artifact is in Workforce-Showcase.

---

## 3. Backend API Endpoint Inventory

**Exact files inspected:** `apps/api/app/api/router.py`, `apps/api/app/api/v1/endpoints/{auth,me,bootstrap,health,...}.py`, `apps/api/app/main.py`

| Route | Method | Source File | Requires Auth | Notes |
|---|---|---|---|---|
| `/api/v1/health` | GET | `health.py` | No | `{"status": "ok"}` |
| `/api/v1/auth/login` | POST | `auth.py` | No | Returns `{access_token, token_type, business_id, user{id,email,is_active}}`; 403 if no active membership |
| `/api/v1/auth/register` | POST | `auth.py` | No | Creates user only (no membership); returns token with no `business_id` |
| `/api/v1/auth/me` | GET | `auth.py` | Yes | Returns `{user{id,email,is_active}, business_id, memberships[{business_id,status,is_owner}], roles, permissions}` |
| `/api/v1/auth/switch-business` | POST | `auth.py` | Yes | Returns `{access_token, token_type, business_id, roles, permissions}` |
| `/api/v1/bootstrap` | POST | `bootstrap.py` | No | Server initialization: creates tenant/business/location/admin user. One-time only. |
| `/api/v1/me/businesses` | GET | `me.py` | Yes | Returns `[{id, name, is_default}]` |
| `/api/v1/me/effective-permissions` | GET | `me.py` | Yes | Returns sorted list of permission codes |
| `/api/v1/rooms` | GET/POST/etc. | `rooms.py` | Yes | — |
| `/api/v1/users` | GET/POST/etc. | `users.py` | Yes | — |
| `/api/v1/employees` | GET/POST/etc. | `employees.py` | Yes | — |
| `/api/v1/tasks` | GET/POST/etc. | `tasks.py` | Yes | — |
| `/api/v1/assignments` | GET/POST/etc. | `assignments.py` | Yes | — |
| `/api/v1/shifts` | GET/POST/etc. | `shifts.py` | Yes | — |

**NOT implemented in Python backend:**
- `GET /api/v1/auth/me/access-context` — only in Showcase local Node.js `api-server`
- Any `GET /bootstrap` returning feature flags — the Python bootstrap is a one-time `POST` only

---

## 4. Backend / Frontend Contract Matrix

**Files inspected:**
- Backend: `apps/api/app/api/v1/endpoints/auth.py`, `apps/api/app/main.py`
- Frontend: `artifacts/workforce-console/src/lib/api-client.ts`, `artifacts/workforce-console/src/lib/auth-context.tsx`
- Spec: `lib/api-spec/openapi.yaml`

| Contract Area | Backend (Python, hn3t.pythonanywhere.com) | Frontend (Showcase workforce-console) | OpenAPI Spec (lib/api-spec/openapi.yaml) | Status | Risk |
|---|---|---|---|---|---|
| **Health check path** | `GET /health` (plain, no `/api/v1` prefix) | Not called directly by frontend | `GET /healthz` | ❌ Mismatch | Spec diverges from both; health checks via monitors may hit wrong path |
| **Login** `POST /auth/login` | Returns `{access_token, token_type, business_id, user{id,email,is_active}}` | `fetchApi("/auth/login")` → uses `access_token` only | Spec: `{access_token, token_type}` only | ⚠️ Partial | Spec incomplete (missing `business_id`, `user`); frontend works because it only reads `access_token` |
| **`GET /auth/me`** | Returns `{user{id,email,is_active}, business_id, memberships[{business_id,status,is_owner}], roles, permissions}` | `fetchApi("/auth/me")` → `mapToSessionInfo()` with defensive fallbacks for both shapes | Spec: `SessionInfo{id,email,first_name,last_name,memberships[{business_id,business_name,role}],active_business_id,roles,permissions}` | ⚠️ Shape diverges | `first_name`/`last_name` not in backend response; `business_name` not in `MembershipSummary`; `business_id` vs `active_business_id` field name; frontend defensive mapping covers this |
| **`POST /auth/switch-business`** | Returns `{access_token, token_type, business_id, roles, permissions}` | `fetchApi("/auth/switch-business")` → uses `access_token` only | Spec: `{access_token, token_type}` | ⚠️ Partial | Spec incomplete; frontend works |
| **`GET /auth/me/access-context`** | ❌ **Not implemented in Python backend** | `fetchApi("/auth/me/access-context")` on startup; caught error → `employmentScope = null` | Spec: `AccessContext{user_id, has_access, scopes[...]}` | ❌ **Gap** — endpoint missing in production | In production without local api-server proxy, `employmentScope` is always `null`; `hasEmployeePermission()` always returns `false` |
| **`POST /api/v1/bootstrap`** | Creates tenant/business/location/admin (one-time init). No `GET` form. | Showcase has a `/bootstrap` page (pre-auth); Console's bootstrap was a `GET` for feature flags | Not documented in spec | ❌ Different contracts — name collision | Confusing; Console's GET bootstrap concept does not map to backend's POST bootstrap |
| **`GET /me/businesses`** | Returns `[{id, name, is_default}]` | Not explicitly called in reviewed auth flow | Not in spec | ⚠️ Unknown consumer | Available but not in spec; not called by Showcase auth flow directly |
| **`GET /me/effective-permissions`** | Returns sorted `string[]` | Not called in auth-context.tsx | Not in spec | ⚠️ Available but unspecified | Useful for runtime permission check but no documented contract |
| **Error shapes** | `{"detail": "..."}` (FastAPI default) + custom shapes | `errorData.detail \|\| errorData.message` fallback handling | `ErrorResponse: {detail: string}` | ✅ Aligned | Both spec and frontend handle `{"detail": ...}` |
| **Bearer token** | `Authorization: Bearer <token>` | `headers.set("Authorization", \`Bearer ${token}\`)` | `bearerAuth` scheme in components | ✅ Aligned | Consistent across all three |
| **`allow_credentials`** | `False` | No `credentials: 'include'` in fetch calls | N/A | ✅ Aligned | `Authorization` header pattern is compatible with `allow_credentials=False` |

---

## 5. CORS / Domain Matrix

**Files inspected:** `apps/api/app/main.py`, `artifacts/workforce-console/.env.example`, `artifacts/workforce-console/vite.config.ts`, `.env.production` (Showcase root)

| Frontend Origin | Backend CORS Allowlist | Status | Notes |
|---|---|---|---|
| `https://hn3t.pythonanywhere.com` (Showcase `.env.production`) | ✅ In allowlist | ✅ Compatible | Production Showcase → Python backend: no CORS error |
| `http://localhost:5173` (Vite dev server) | ✅ In allowlist | ✅ Compatible | Dev mode uses Vite proxy anyway; direct-mode also works |
| `http://localhost:3000` | ✅ In allowlist | ✅ Compatible | — |
| `https://wf-hn3t.pythonanywhere.com` | ✅ In allowlist | ✅ Origin present | Secondary backend domain |
| `https://api-hn3t.pythonanywhere.com` (render.yaml `NEXT_PUBLIC_API_BASE_URL`) | ❌ NOT in allowlist | ❌ Mismatch | This is from Workforce-backup's embedded Next.js config (`apps/web/hospitable-web`) — not Showcase. That Next.js frontend would have CORS errors in production if deployed via Render. |
| Local api-server (port 8080 in Vite proxy) | Internal proxy; not cross-origin | ✅ No CORS issue | Dev-only forwarding; CORS is on Python backend |

**CORS policy conclusion:** Workforce-Showcase frontend is CORS-compatible with the Python backend in production. The prior report's CORS blocker is specific to the embedded Next.js frontend in Workforce-backup, which is not the Showcase app.

**`CORS_ALLOW_ORIGINS` env var:** Backend will use the env var if set; if absent, defaults to the hardcoded list above. Adding any new frontend domain requires either setting this env var on PythonAnywhere or adding it to `main.py`.

---

## 6. RBAC / Membership Check

**Files inspected:** `apps/api/app/api/v1/endpoints/auth.py`, `apps/api/app/services/rbac_service.py`, `artifacts/workforce-console/src/lib/auth-context.tsx`

### 6.1 Backend RBAC Model (Active)

The active runtime RBAC model uses the canonical local access control tables:

| Table | Role |
|---|---|
| `users` | Auth identity |
| `memberships` | Links user to business (`status`, `is_owner`) |
| `roles` | Role definitions per business |
| `role_permissions` | Maps roles to permission codes |
| `scoped_role_assignments` | Assigns roles to memberships with optional `location_id` scope |

`rbac_service.get_effective_role_names()` and `get_effective_permission_codes()` query these tables. **No `biz_roles` tables are used in the active auth flow** — the prior concern about dual RBAC is resolved at the service layer, though the legacy `biz_roles` migration entries may still exist.

### 6.2 Frontend RBAC Model

The frontend maintains two separate permission layers:
1. **Session permissions** (from `GET /auth/me`): `session.permissions` / `session.roles` — sourced from Python backend's RBAC tables
2. **Employment scope permissions** (from `GET /auth/me/access-context`): `employmentScope.effective_permissions` — sourced from **local SQLite DB via Node.js api-server proxy only**

| Check | Method | Source | Backend Path | Risk |
|---|---|---|---|---|
| `hasPermission(p)` | Checks `session.permissions` | Python backend RBAC | `/api/v1/auth/me` | ✅ Works in production |
| `hasRole(r)` | Checks `session.roles` | Python backend RBAC | `/api/v1/auth/me` | ✅ Works in production |
| `isOwner()` | Checks roles + permissions | Python backend RBAC | `/api/v1/auth/me` | ✅ Works in production |
| `isSuperAdmin()` | Checks roles/permissions + `is_superadmin` flag | Python backend RBAC | `/api/v1/auth/me` | ⚠️ Backend does not return `is_superadmin`; relies on role/permission check only |
| `hasEmployeePermission(p)` | Checks `employmentScope.effective_permissions` | Local api-server SQLite | `/api/v1/auth/me/access-context` | ❌ Returns `false` in production (endpoint missing) |

**RBAC integrity assessment:** Session-level permission checks are safe. Employment-scope checks silently degrade in production (not a bypass — gates that use `hasEmployeePermission` will deny by default). No RBAC bypass was observed.

### 6.3 Screens Depending on RBAC

| Screen | Permission Pattern | Risk |
|---|---|---|
| `/app/dashboard` | None observed (info display) | Low |
| `/app/users` | Owner check implied by route | Medium |
| `/app/employees` | Employment scope (local only) | ❌ Degrades in production |
| `/app/shifts`, `/app/assignments` | RBAC via backend | ✅ Works |
| `/app/studio` | Unknown — Studio module | Unknown |
| `/superadmin/project-manager` | `isSuperAdmin()` check | ⚠️ Depends on superadmin role/permission |

---

## 7. Deployment / CI Matrix

| Repo | Deploy Target | Runtime | CI Status | CI Failure Cause |
|---|---|---|---|---|
| Workforce-backup | PythonAnywhere (`hn3t.pythonanywhere.com`) | Python/WSGI + a2wsgi | ⚠️ CI in progress at eval time; tests pass locally | Latest run in_progress |
| Workforce-Showcase | PythonAnywhere (Flask SPA server via `app.py`) | Node 20 + pnpm + Vite (build) → Flask (serve) | ❌ All CI runs failing (12/12) | `pyproject.toml changed significantly since poetry.lock was last generated` — lock file stale |
| Workforce-Console | PythonAnywhere / Replit (devhub context) | pnpm workspace | Unknown — no recent run data | N/A |

### Showcase CI Fix
The Showcase CI failure is straightforward: `poetry lock --no-update` (or `poetry lock`) must be re-run against the updated `pyproject.toml` and the result committed. The build itself may be valid; only the Python dependency lock is stale.

### Deploy pipeline (Showcase)
1. `pnpm build` in `artifacts/workforce-console` → outputs to `dist/public`
2. `app.py` Flask server reads `FRONTEND_DIST_DIR` (or `./dist`) and serves the SPA
3. `deploy-to-pythonanywhere.yml` workflow handles the deployment

### PythonAnywhere-specific assumptions
- `app.py` is a standard WSGI-compatible Flask server — no PythonAnywhere-specific API used
- `wsgi.py` in Workforce-backup wraps FastAPI via `a2wsgi` for PythonAnywhere's WSGI execution model
- `X-Forwarded-*` header support added to FastAPI app (`ProxyHeadersMiddleware`) to preserve HTTPS scheme

---

## 8. Test / Build Check

### Workforce-backup
```
Command: PYTHONPATH=apps/api SKIP_WORKFORCE_MODELS=1 python -m pytest -q tests
Result:  53 passed, 44 warnings in 8.26s  ✅
Warnings: SECRET_KEY env var not set (runtime warning, not a test failure)
```

### Workforce-Showcase
- **Install blocker:** `pyproject.toml changed significantly since poetry.lock was last generated`
- Dependencies could not be installed in CI; no build was run
- Fix: `cd Workforce-Showcase && poetry lock` then commit `poetry.lock`
- Vite/pnpm build itself not tested; no known type errors from inspection

### Workforce-Console
- No test command run; no `package.json` tests script found
- `workforce_frontend_app/scripts/smoke-bootstrap.mjs` is a smoke test that was run against local uvicorn; cannot be run cross-repo

---

## 9. Cross-Repo Compatibility Matrix

| Compatibility Area | Status | Evidence | Risk | Required Action |
|---|---|---|---|---|
| API base URL | ✅ Compatible | Showcase `.env.production` = `https://hn3t.pythonanywhere.com`; in CORS allowlist | Low | None |
| CORS | ✅ Compatible for Showcase | `hn3t.pythonanywhere.com` in allowlist; `allow_credentials=False` OK with Bearer tokens | Low for Showcase. ❌ Broken for Next.js frontend in backup's render.yaml | Fix render.yaml if Next.js frontend is deployed |
| `POST /auth/login` | ✅ Compatible (with caveats) | Frontend reads `access_token` only; extra fields (`business_id`, `user`) in backend response are unused by frontend | Low | Update OpenAPI spec to reflect actual backend response |
| `GET /auth/me` | ⚠️ Shape diverges | Backend: `{user{id,email,is_active}, business_id, memberships[{business_id,status,is_owner}]}`; Frontend: defensively maps both shapes | Medium (fragile) | Align backend MeResponse to include `first_name`, `last_name` in UserSummary; add `business_name` to MembershipSummary; or update spec to match backend |
| `GET /auth/me/access-context` | ❌ Gap | Only in Node.js local proxy; not in Python backend | High — employment scope silently fails in production | Either implement endpoint in Python backend, or document that employment scope requires the local api-server proxy |
| `POST /bootstrap` | ❌ Contract collision | Backend bootstrap = one-time server init (POST). Console/Copilot context assumed GET feature-flags. | Medium — conceptual confusion | Rename or document distinction. Consider `GET /api/v1/features` or `GET /api/v1/session-context` for the feature-flag use case. |
| Session-level RBAC | ✅ Aligned | Both use canonical `roles`/`scoped_role_assignments` tables via rbac_service | Low | None |
| Employment-scope RBAC | ❌ Gap | Employment scope requires local SQLite DB seeded separately; no migration path defined | High in production | Define production path: either Python backend implements user_employee_links tables and access-context endpoint, or document that employment scope is dev-only |
| Error shapes | ✅ Aligned | Both use `{"detail": ...}` | Low | None |
| Bearer token auth | ✅ Aligned | `Authorization: Bearer` header; no credentials cookie | Low | None |
| OpenAPI spec accuracy | ❌ Outdated | `lib/api-spec/openapi.yaml` describes `SessionInfo` and `LoginResponse` that do not match backend schemas; `/healthz` vs `/health` mismatch | Medium | Update spec to reflect actual backend contracts |
| CI/CD | ❌ Broken for Showcase | Showcase CI failing since 2026-04-11 (poetry.lock stale) | High — no automated validation | `poetry lock` and commit; fix CI |

---

## 10. Highest-Priority Fixes

1. **[P0] Fix Showcase CI** — Run `poetry lock` in Showcase repo, commit updated `poetry.lock`. CI has been broken since at least 2026-04-11. No code validation is running. Fix: `poetry lock --no-update` in repo root.

2. **[P1] Implement or proxy `GET /api/v1/auth/me/access-context` in Python backend** — The frontend calls this at startup. Without it, `hasEmployeePermission()` always returns `false` in production. Options:
   - Implement the user-employee link + access-context endpoint in Python backend (proper solution)
   - Add explicit documentation that this feature requires the local api-server proxy and is dev-only
   - Until resolved, any screen that uses `hasEmployeePermission()` should not be deployed as production-ready

3. **[P1] Align `MeResponse` schema** — Add `first_name`, `last_name` to `UserSummary` in the Python backend auth endpoint, and add `business_name` to `MembershipSummary`. The frontend defensive mapping works today but will break if the mapping code is simplified or the spec drives generated types.

4. **[P2] Update `lib/api-spec/openapi.yaml`** — Bring the spec in sync with the actual Python backend:
   - `/healthz` → `/health`
   - `LoginResponse` — add `business_id` and `user`
   - `SessionInfo` — update to match `MeResponse` shape
   - Add `GET /auth/me/access-context` with a clear note about upstream support gap

5. **[P2] Resolve `render.yaml` CORS blocker** — The embedded Next.js frontend in Workforce-backup targets `api-hn3t.pythonanywhere.com` which is not in the CORS allowlist. Either add the origin to the allowlist or update `render.yaml` to target `hn3t.pythonanywhere.com`.

6. **[P3] Name the bootstrap distinction** — `POST /api/v1/bootstrap` (server init) vs a potential `GET /api/v1/session-context` (feature flags / session warmup) should be clearly separated. The current naming is misleading.

---

## 11. Phase 0 Foundation Tag Assessment

**Is the Phase 0 foundation tag (`foundation-v0.1`) still justified?**

**Yes, with qualification.** The backend foundation is stable and tested (53/53 passing), canonical RBAC is active, tenant/business/location/membership model is in place, and the primary frontend targets the correct domain. Phase 0 is appropriately described as "Foundation Freeze."

**What is NOT Phase 0 ready:**
- Employment scope / access-context endpoint (requires Phase 1 work to implement server-side)
- Showcase CI is broken (must be fixed before cutting a tag on that repo)
- OpenAPI spec is out of sync (should be updated before external consumers rely on it)
- Embedded Next.js frontend CORS issue in render.yaml (if that deployment is intended)

**Recommended tag sequence:**
1. Fix Showcase CI (poetry.lock)
2. Align `/auth/me` schema (add `first_name`/`last_name` to backend) — small, safe change
3. Update `openapi.yaml` spec
4. Cut `foundation-v0.1` on Workforce-backup after CI passes
5. Declare Phase 1 goal: implement `user_employee_links` and `GET /auth/me/access-context` in Python backend

---

## 12. Files Inspected

### Workforce-backup
- `apps/api/app/main.py` — CORS, app init
- `apps/api/app/api/router.py` — route inclusion
- `apps/api/app/api/v1/endpoints/auth.py` — auth routes + schema shapes
- `apps/api/app/api/v1/endpoints/me.py` — /me/businesses, /me/effective-permissions
- `apps/api/app/api/v1/endpoints/bootstrap.py` — server bootstrap
- `render.yaml` — deployment config
- `docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT.md` — prior report (baseline)

### Workforce-Showcase
- `/` (root) — directory structure
- `.env.production` — production API URL
- `app.py` — Flask SPA server
- `package.json` — workspace root scripts
- `lib/api-spec/openapi.yaml` — OpenAPI spec (15KB)
- `lib/api-client-react/src/custom-fetch.ts` — HTTP client implementation
- `artifacts/workforce-console/.env.example` — env documentation
- `artifacts/workforce-console/vite.config.ts` — Vite + proxy config
- `artifacts/workforce-console/package.json` — app dependencies
- `artifacts/workforce-console/src/App.tsx` — routing + auth guards
- `artifacts/workforce-console/src/lib/api-client.ts` — API fetch wrapper
- `artifacts/workforce-console/src/lib/auth-context.tsx` — auth + RBAC context
- `artifacts/api-server/src/app.ts` — Node.js proxy app
- `artifacts/api-server/src/auth/router.ts` — auth proxy routes (including access-context)
- `.github/workflows/ci.yml` — CI workflow (via actions API)

### Workforce-Console
- `/` — directory structure
- `PROGRESS_REPORT.md` — development history
- `workforce_frontend_app/artifacts/workforce-console/` — artifact directory
- `docs/` — planning docs structure
- `.github/workflows/ci.yml`, `validate-employee-link-editable-install.yml` — CI workflows

---

*Previous report (`WORKFORCE_CROSS_REPO_EVALUATION_REPORT.md`) placeholder sections for workforce-showcase and workforce-console are superseded by this document.*
