# Workforce Cross-Repo Evaluation Report

**Generated:** 2026-05-03  
**Coordination repo:** `workforce-backup`  
**Analyst:** GitHub Copilot automated evaluation

> ⚠️ **SUPERSEDED** — This report contained placeholder sections for Workforce-Showcase and Workforce-Console because both repos were inaccessible at the time of writing. A full evaluation with real findings for all three repos is in:
> **`docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT_2026-05-03.md`**

---

## Repo Access Summary

| Repo | Access | Notes |
|---|---|---|
| workforce-backup | ✅ Available (cloned locally) | Full analysis performed |
| workforce-showcase | ❌ Inaccessible (404 — not found or private) | Placeholder sections only |
| workforce-console | ❌ Inaccessible (404 — not found or private) | Placeholder sections only |

> **Note:** Only `workforce-backup` was directly accessible during this evaluation. Sections covering `workforce-showcase` and `workforce-console` contain placeholder text that must be filled in by pasting the content from each repo's own `docs/reports/REPO_EVALUATION_REPORT.md` once those reports are generated.

---

## 1. Executive Summary

### Overall System Health: 🟡 Early Foundation — Not Production-Ready

The Workforce platform is in **Phase 0 (Foundation Freeze)** — actively stabilizing its code structure, migration surface, model registration, and import paths. The backend is functional at a basic level (52 tests passing, `/health` endpoint operational, auth + membership flows verified), but critical infrastructure is incomplete or unstable:

- **Top Blockers:**
  1. Dual RBAC system — planned tables exist but are orphaned; the active system uses a divergent schema (`biz_roles` / `biz_role_permissions` / `membership_location_roles`). These must be reconciled before any frontend integration or deployment hardening.
  2. Dual Python import roots (`app` vs `apps/api/app`) — the canonical path is `apps/api/app`, but `SKIP_WORKFORCE_MODELS=1` is required at boot to prevent double-registration, indicating the two roots still conflict.
  3. Alembic migration graph has a no-op merge head — indicates the migration history diverged and was patched with a reconciliation commit. Migration safety on production PostgreSQL is unverified.
  4. Audit and event tables are not yet built (Phase 2 not started) — no durable change trail.
  5. `workforce-showcase` and `workforce-console` are not accessible — cross-repo compatibility cannot be confirmed; frontend/backend contract alignment is a known unknown.

- **Top Risks:**
  1. Frontend env (`NEXT_PUBLIC_API_BASE_URL=https://api-hn3t.pythonanywhere.com`) in render.yaml does not match any domain in the backend CORS allowlist, creating a likely CORS failure in production.
  2. CORS is configured with `allow_credentials=False` while the auth flow relies on session tokens — this may force insecure token handling patterns in the browser client.
  3. The WSGI entrypoint wraps an ASGI app (`a2wsgi`) on PythonAnywhere — performance and async compatibility risks under load.
  4. Dev SQLite backup files (`dev.db.*.bak`) are tracked in git — leaks local DB state into repo history.
  5. No production PostgreSQL migration path has been verified — current SQLite-only testing may mask migration compatibility issues.

- **Top Recommended Next Steps:**
  1. Reconcile the dual RBAC schema — either adopt the active `biz_roles` tables as canonical and drop/archive the orphaned planned tables, or migrate to the planned tables.
  2. Fix CORS: add `api-hn3t.pythonanywhere.com` (or the actual frontend origin) to the CORS allowlist and determine the correct `allow_credentials` policy.
  3. Create the Phase 0 foundation tag (`foundation-v0.1`) to checkpoint current stable state.
  4. Publish individual `REPO_EVALUATION_REPORT.md` files for `workforce-showcase` and `workforce-console` and populate the placeholder sections below.
  5. Begin Phase 1 formally: define the canonical tenant/business/location/membership/permission schema and unify the RBAC tables.

---

## 2. Repo Health Matrix

| Repo | Purpose | Health | Production Readiness | Biggest Risk | Next Step |
|---|---|---|---|---|---|
| workforce-backup | Backend API + frontend (hospitable-web). Platform core and canonical runtime source. | 🟡 Stabilizing (Phase 0) | ❌ Not ready — dual RBAC, migration divergence, CORS misconfiguration | Dual RBAC schema creates contract ambiguity for all frontend consumers | Reconcile RBAC tables; fix CORS; cut Phase 0 tag |
| workforce-showcase | _(placeholder — repo inaccessible)_ | ❓ Unknown | ❓ Unknown | ❓ Unknown | Publish repo evaluation report |
| workforce-console | _(placeholder — repo inaccessible)_ | ❓ Unknown | ❓ Unknown | ❓ Unknown | Publish repo evaluation report |

---

## 3. Cross-Repo Compatibility Matrix

> Items marked ❓ are unknowns because `workforce-showcase` and `workforce-console` are inaccessible.

| Compatibility Area | Status | Evidence | Risk | Required Action |
|---|---|---|---|---|
| Backend API contracts | ⚠️ Partial / Unknown | workforce-backup has versioned `/api/v1/` prefix; no OpenAPI client generated for other repos | Unknown consumers may use wrong base path | Generate and publish OpenAPI schema from workforce-backup; confirm consumers |
| Frontend API clients | ❓ Unknown | workforce-showcase and workforce-console inaccessible | Clients may target wrong API base URL or schema version | Access repos and audit API client configuration |
| Auth / login flow | ⚠️ Partial | workforce-backup: `POST /api/v1/auth/login` requires active membership (returns 403 without one); JWT-based | Frontend login flow may not handle 403-no-membership vs 401-bad-credentials distinction correctly | Confirm frontend error handling for auth states |
| User / session model | ⚠️ Partial | workforce-backup: User = auth identity, Membership = business membership. A registered user without membership cannot log in | Frontend may assume registration = access | Confirm frontend post-registration UX handles the no-membership gate |
| RBAC expectations | ❌ Mismatched internally | workforce-backup has two parallel RBAC systems; the active system uses `biz_roles`/`membership_location_roles`, not the planned `roles`/`user_role_assignments` | Frontend consumers expecting one RBAC schema will get a different one | Reconcile RBAC schema; publish definitive permission model |
| Employee / user separation | ⚠️ Partial | workforce-backup models User (auth) separately from Worker/Employee profile; linking model in progress | Frontends may conflate user and employee lookups | Confirm `/api/v1/me` returns correct combined representation |
| Environment variables | ❌ Mismatch | render.yaml: `NEXT_PUBLIC_API_BASE_URL=https://api-hn3t.pythonanywhere.com`; not present in CORS allowlist (`hn3t.pythonanywhere.com`, `wf-hn3t.pythonanywhere.com`) | CORS rejection in production | Add correct frontend origin to CORS list; audit all env configs |
| Deployment domains | ⚠️ Inconsistent | Backend: `hn3t.pythonanywhere.com` / `wf-hn3t.pythonanywhere.com`; Frontend render target: `api-hn3t.pythonanywhere.com` | Domain confusion across repos | Publish definitive domain map for all services |
| Build systems | ❌ Fragmented | workforce-backup: Poetry (Python) + pnpm (Next.js); WSGI on PythonAnywhere + Render for frontend | Two deployment targets for one repo; untested CI pipeline | Consolidate deployment strategy; add CI |
| Generated types / schemas | ❌ None found | No OpenAPI client generation found in any accessible repo | Frontend consumers use hand-rolled or guessed contracts | Generate OpenAPI schema; generate TypeScript client from it |
| CI / CD | ❌ None found in workforce-backup | No `.github/workflows/` CI config found | Regressions may go undetected | Add GitHub Actions CI for backend tests |
| Docs / devhub / showcase links | ❓ Unknown | docs/ exists in workforce-backup; devhub and showcase repos inaccessible | Docs may be stale or siloed | Access showcase/console repos and audit cross-linking |

---

## 4. Backend / Frontend Contract Alignment

> Contract analysis is based on workforce-backup source. Frontend assumptions from `apps/web/hospitable-web` in this repo only; workforce-showcase and workforce-console assumptions are unknown.

| Contract Area | Backend (workforce-backup) | Frontend Known Config | Status | Risk | Required Action |
|---|---|---|---|---|---|
| Login endpoint | `POST /api/v1/auth/login` | `NEXT_PUBLIC_API_URL=http://localhost:8000` (dev only; no prod value in .env.example) | ⚠️ Unconfirmed in prod | Wrong base URL in prod | Set `NEXT_PUBLIC_API_URL` to actual backend URL in prod config |
| `/auth/me` endpoint | `GET /api/v1/me` (effective-permissions added 2026-04-28); no explicit `/auth/me` route found | Unknown | ❓ Unknown | Frontend may call wrong me endpoint | Confirm canonical `/me` or `/auth/me` route; align frontend |
| Registration / create-user | `POST /api/v1/auth/register` creates user only — no business or membership. `POST /api/v1/users/` with `business_id` creates user + membership | Unknown | ⚠️ Partial | Frontend may assume `/register` gives immediate login access | Confirm frontend registration flow handles membership-gate |
| Employee / user linking | User model has `business_id` FK; Membership table links user to business; Worker/Employee profile separate | Unknown | ❓ Unknown | Frontend may not know how to link employee and user identities | Publish `/api/v1/employees` or `/api/v1/me/profile` contract |
| Business / location scoping | Most routes accept optional `location_id` query param for scoped permission checks | Unknown | ❓ Unknown | Frontend may not pass location scope, returning false permission denials | Document all scoped endpoints; ensure frontend passes location context |
| Role / permission | Active: `biz_roles` → `biz_role_permissions` → `Permission.key` (e.g., `schedule:read`). Planned but unused: `roles` / `user_role_assignments` | Unknown | ❌ Mismatch risk | Frontend calling permission APIs may hit wrong model | Deprecate orphaned tables; confirm canonical permission model with frontend team |
| Error response shapes | FastAPI default: `{"detail": "..."}` for HTTP exceptions | Unknown | ⚠️ Assumed | Frontend may not handle all error shapes consistently | Publish error shape contract; confirm frontend handles `{"detail": ...}` |
| CORS / frontend origin | Allowlist: `https://hn3t.pythonanywhere.com`, `https://wf-hn3t.pythonanywhere.com`, localhost variants. `allow_credentials=False` | render.yaml: `NEXT_PUBLIC_API_BASE_URL=https://api-hn3t.pythonanywhere.com` | ❌ Mismatch | CORS failure in production | Add correct frontend origin; set `allow_credentials` policy |
| API base URL | `/api/v1/` prefix on all routes | `NEXT_PUBLIC_API_URL=http://localhost:8000` (dev) | ⚠️ Dev only | Production URL not set in tracked config | Set and document production API base URL |

### Summary

- **Confirmed alignments:** FastAPI `/api/v1/` prefix; JWT auth; `{"detail": ...}` error shapes (FastAPI default)
- **Confirmed mismatches:** CORS origin mismatch between render.yaml frontend URL and backend allowlist
- **Unknowns:** All contracts for workforce-showcase and workforce-console; canonical `/me` endpoint path; employee/user link API; frontend error handling
- **Required contract specs:** OpenAPI schema publication; canonical domain map; CORS policy decision; permission model decision

---

## 5. Deployment Readiness Matrix

| Component | Domain / Target | Build / Runtime | Env Vars | Health Check | Status | Blockers |
|---|---|---|---|---|---|---|
| workforce-backup API (PythonAnywhere) | `https://hn3t.pythonanywhere.com` / `https://wf-hn3t.pythonanywhere.com` | Python 3.x + Poetry + a2wsgi WSGI wrapper | `DATABASE_URL`, `SKIP_WORKFORCE_MODELS`, `CORS_ALLOW_ORIGINS`, `WORKFORCE_ENV_FILE`, `ENV` | `GET /health → {"status":"ok"}` | ⚠️ Partially deployed | CORS mismatch; WSGI async wrap risk; no CI; no prod PostgreSQL migration verified |
| workforce-backup frontend (Render) | Not confirmed (Render free plan) | Node 20 + pnpm + Next.js | `NEXT_PUBLIC_API_BASE_URL=https://api-hn3t.pythonanywhere.com`, `NEXT_PUBLIC_LOCATION_ID` | None found | ❌ Not ready | `NEXT_PUBLIC_API_BASE_URL` not in CORS allowlist; `NEXT_PUBLIC_LOCATION_ID` requires seed script output |
| `https://devhub-hn3t.pythonanywhere.com` | `https://devhub-hn3t.pythonanywhere.com` | Unknown | Unknown | Unknown | ❓ Unknown | Cannot assess — workforce-showcase and workforce-console inaccessible |
| workforce-showcase | Unknown | Unknown | Unknown | Unknown | ❓ Unknown | Repo inaccessible |
| workforce-console | Unknown | Unknown | Unknown | Unknown | ❓ Unknown | Repo inaccessible |

---

## 6. Security / RBAC / Data Integrity Summary

### Auth
- JWT-based authentication is implemented in workforce-backup.
- Login correctly requires an active Membership — users without membership receive a clear 403.
- `allow_credentials=False` in CORS: if the frontend uses cookies or HTTP-only token storage, this will block credential exchange. If using `Authorization: Bearer` headers only, this is fine — but the policy must be intentionally documented.
- No explicit token expiry, refresh token endpoint, or token revocation found in the accessible codebase.

### RBAC
- **Critical risk:** Two parallel RBAC systems exist. The planned tables (`roles`, `permissions`, `role_permissions`, `user_role_assignments`) are created by migration but **not used**. The active system (`biz_roles`, `biz_role_permissions`, `membership_location_roles`) is used in runtime code. This creates a permanent migration archaeology problem and confuses any external consumer reading the schema.
- `GET /api/v1/me/effective-permissions` was added 2026-04-28 — confirms intent to expose permissions to the frontend, but the underlying table is the active (not planned) RBAC system.

### Tenant / Business / Location Scoping
- Most routes accept `location_id` query param for scoped permission resolution.
- `tenant_id` is on business records; `location_id` is on operational records.
- Scoping is enforced at the dependency injection layer (`app/api/permissions.py`).
- Risk: optional location scoping means a missing `location_id` may silently degrade access checks to business-level only.

### User / Employee Separation
- User = auth identity (`users` table, `hashed_password`, `is_active`).
- Employee / Worker Profile = operational identity (separate model, not yet fully linked in accessible code).
- Risk: a User without an Employee profile may not be displayable in scheduling or task UI.

### Admin Tooling
- Admin-invite and admin-create-with-membership endpoints exist.
- No admin-only route guard audited for robustness in this pass. Confirm admin endpoints require `is_superuser` or equivalent.

### CORS
- Hardcoded CORS allowlist with no environment override default — the `CORS_ALLOW_ORIGINS` env var exists but defaults to a hardcoded list if absent.
- `api-hn3t.pythonanywhere.com` (frontend target from render.yaml) is **not** in the allowlist.

### Secrets / Deployment Config
- `.env*` files are gitignored (D-0005).
- Dev SQLite backup files (`dev.db.*.bak`) are present in the repo root and should be gitignored or removed.
- No secrets appear to be hardcoded in the reviewed source.

### Generated Files / Public-Private Boundary
- No OpenAPI client generation detected.
- `index.html`, `index.html.bak`, `index.html.merged` present in repo root — likely a legacy frontend artifact; should be audited and archived.

---

## 7. Documentation / Source-of-Truth Summary

| Doc | Location | Status | Recommendation |
|---|---|---|---|
| `HN3T_MASTER_PLAN.md` | `docs/plans/HN3T_MASTER_PLAN.md` | ✅ Canonical master plan | Keep; link from README |
| `MASTER_PLAN.md` | `docs/plans/MASTER_PLAN.md` | ⚠️ Legacy stub redirecting to HN3T_MASTER_PLAN | Keep redirect; do not update directly |
| `ARCHITECTURE.md` | `docs/ARCHITECTURE.md` | ✅ High-level architecture | Keep; expand with canonical runtime surface diagram |
| `DECISIONS.md` | `docs/DECISIONS.md` | ✅ Active decision log | Keep; add RBAC reconciliation decision |
| `CHANGELOG.md` | `docs/CHANGELOG.md` | ✅ Active | Keep |
| `WORKLOG.md` | `docs/WORKLOG.md` | ✅ Active | Keep |
| `RBAC_IMPLEMENTATION_AUDIT.md` | `docs/rbac/RBAC_IMPLEMENTATION_AUDIT.md` | ✅ Valuable audit | Keep; link from DECISIONS.md; surface in showcase/devhub |
| `PHASE_STATUS.md` | `docs/PHASE_STATUS.md` | ✅ Active | Keep; update when Phase 0 tag is cut |
| `TODO.md` | `docs/TODO.md` | ✅ Active | Keep |
| `ROADMAP.md` | `docs/ROADMAP.md` | ✅ Active | Keep |
| `MIGRATION_PLAN.md` | `docs/MIGRATION_PLAN.md` | ⚠️ May be stale — see DECISIONS.md for migration history | Review and update with current Alembic state |
| `DOMAIN_MODEL.md` | `docs/DOMAIN_MODEL.md` | ✅ Good overview | Keep; should be surfaced in devhub/showcase |
| `API_BOUNDARIES.md` | `docs/API_BOUNDARIES.md` | ✅ Good overview | Keep; should be surfaced in devhub/showcase |
| `MODULE_CATALOG.md` | `docs/MODULE_CATALOG.md` | ✅ Inventory | Keep; expand with implementation status per module |
| `RECOVERY_PLAYBOOK.md` | `docs/RECOVERY_PLAYBOOK.md` | ✅ Critical | Keep; review for current deployment paths |
| `PROJECT_OPERATING_SYSTEM.md` | `docs/PROJECT_OPERATING_SYSTEM.md` | ✅ Foundation | Keep |
| `MASTER_PLAN_DRAFT.md` | `docs/plans/MASTER_PLAN_DRAFT.md` | ⚠️ Draft — may overlap with canonical plan | Review; merge into HN3T_MASTER_PLAN or archive |
| `REPO_EVALUATION_REPORT.md` | `docs/reports/` — **missing** | ❌ Missing for this repo | Create `docs/reports/REPO_EVALUATION_REPORT.md` for workforce-backup |
| workforce-showcase docs | Inaccessible | ❓ Unknown | Access repo; audit docs |
| workforce-console docs | Inaccessible | ❓ Unknown | Access repo; audit docs |

**Missing docs:**
- `docs/reports/REPO_EVALUATION_REPORT.md` for each of the three repos
- OpenAPI schema or published API reference
- Canonical domain map (which subdomain serves what)
- CORS policy decision document
- RBAC reconciliation decision (planned tables vs active tables)
- Environment variable reference for all deployment targets

**Best source-of-truth docs (ready to surface in devhub/showcase):**
- `docs/rbac/RBAC_IMPLEMENTATION_AUDIT.md`
- `docs/DOMAIN_MODEL.md`
- `docs/API_BOUNDARIES.md`
- `docs/plans/HN3T_MASTER_PLAN.md`

---

## 8. Top 10 Risks

| Rank | Risk | Repos Affected | Severity | Evidence | Recommended Fix |
|---|---|---|---|---|---|
| 1 | Dual RBAC schema — orphaned planned tables vs active biz_roles system | workforce-backup (and any consumer) | 🔴 Critical | `docs/rbac/RBAC_IMPLEMENTATION_AUDIT.md`; `app/models/identity.py` vs migration `zz_add_rbac_tables` | Make a formal DECISIONS.md entry; deprecate orphaned tables; update all consumers |
| 2 | CORS mismatch — frontend Render target `api-hn3t.pythonanywhere.com` not in backend allowlist | workforce-backup | 🔴 Critical | `apps/api/app/main.py` CORS origins vs `render.yaml` NEXT_PUBLIC_API_BASE_URL | Add correct origin to CORS list; document domain map |
| 3 | No CI/CD pipeline | workforce-backup | 🟠 High | No `.github/workflows/` found | Add GitHub Actions CI for pytest + lint |
| 4 | Dual Python import roots (`app` vs `apps/api/app`) + SKIP_WORKFORCE_MODELS flag | workforce-backup | 🟠 High | `wsgi.py`, `apps/api/app/main.py` `os.environ.setdefault("SKIP_WORKFORCE_MODELS", "1")` | Remove duplicate root import surface; retire the flag once resolved |
| 5 | No production PostgreSQL migration verified | workforce-backup | 🟠 High | All testing on SQLite; batch mode used for SQLite-specific ALTER TABLE constraints | Test migrations on PostgreSQL before deploying |
| 6 | workforce-showcase and workforce-console inaccessible — all cross-repo assumptions unconfirmed | All three repos | 🟠 High | GitHub API 404 for both repos | Access repos; complete individual REPO_EVALUATION_REPORT.md files |
| 7 | Dev SQLite backup files committed in repo root | workforce-backup | 🟡 Medium | `dev.db.*.bak` files in repo root directory listing | Add `*.bak` and `dev.db*` to `.gitignore`; remove tracked files |
| 8 | Alembic merge revision is a no-op patch over diverged heads | workforce-backup | 🟡 Medium | `docs/DECISIONS.md` migration-2026-04-24; `alembic/versions/merge_0002_20260420_proper.py` | Review migration graph; ensure linear upgrade path on fresh DB |
| 9 | `allow_credentials=False` CORS policy with Bearer-token auth — policy not documented | workforce-backup (and any consumer) | 🟡 Medium | `apps/api/app/main.py` `allow_credentials=False` | Document auth/CORS policy explicitly; confirm frontend uses Authorization header |
| 10 | Legacy frontend artifacts in repo root (`index.html`, `index.html.bak`, `index.html.merged`) | workforce-backup | 🟡 Medium | Files present in repo root listing | Audit and archive or remove legacy HTML files |

---

## 9. Top 10 Recommended Next Actions

| Rank | Priority | Repo | Task | Why It Matters |
|---|---|---|---|---|
| 1 | 🔴 Immediate | workforce-backup | Reconcile the dual RBAC schema — make a formal DECISIONS.md entry, choose canonical tables, deprecate orphaned tables | Every downstream consumer is blocked by RBAC ambiguity |
| 2 | 🔴 Immediate | workforce-backup | Fix CORS: add the correct frontend production origin to the CORS allowlist and document the `allow_credentials` policy | CORS mismatch causes production fetch failures |
| 3 | 🟠 High | workforce-showcase, workforce-console | Gain access to both repos and create `docs/reports/REPO_EVALUATION_REPORT.md` for each | Cannot assess cross-repo compatibility without access |
| 4 | 🟠 High | workforce-backup | Add GitHub Actions CI (pytest + flake8) to prevent regressions | 52 tests pass locally but no CI guards the main branch |
| 5 | 🟠 High | workforce-backup | Cut the Phase 0 foundation tag (`foundation-v0.1`) and formally move to Phase 1 | Phase 0 exit criteria are largely met; tagging creates a recovery checkpoint |
| 6 | 🟠 High | workforce-backup | Publish OpenAPI schema (can use `fastapi --app apps.api.app.main:app openapi`) and pin a TypeScript client generation step | Eliminates hand-rolled frontend contract guessing |
| 7 | 🟠 High | workforce-backup | Remove or gitignore `dev.db.*.bak` files from repo root | Leaks local state; pollutes history |
| 8 | 🟡 Medium | workforce-backup | Verify Alembic migration chain on a fresh PostgreSQL instance | SQLite batch-mode migrations may not translate cleanly |
| 9 | 🟡 Medium | workforce-backup | Create `docs/reports/REPO_EVALUATION_REPORT.md` for workforce-backup itself | Completes the report inventory and provides baseline for future evaluations |
| 10 | 🟡 Medium | All | Publish a definitive domain map (which subdomain → which service) | Domain confusion (`hn3t.pythonanywhere.com` vs `wf-hn3t.pythonanywhere.com` vs `api-hn3t.pythonanywhere.com`) is a repeated source of deployment misconfiguration |

---

## 10. Report Inventory

| Report | Location | Status |
|---|---|---|
| workforce-backup repo evaluation | `workforce-backup/docs/reports/REPO_EVALUATION_REPORT.md` | ❌ Does not exist yet — needs to be created |
| workforce-showcase repo evaluation | `workforce-showcase/docs/reports/REPO_EVALUATION_REPORT.md` | ❌ Inaccessible — repo returns 404 |
| workforce-console repo evaluation | `workforce-console/docs/reports/REPO_EVALUATION_REPORT.md` | ❌ Inaccessible — repo returns 404 |
| This cross-repo report | `workforce-backup/docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT.md` | ✅ Created |

---

## Placeholder Sections — To Be Filled In

The following sections must be updated once `workforce-showcase` and `workforce-console` are accessible and their individual REPO_EVALUATION_REPORT.md files are generated.

### Workforce-Showcase Repo Report Placeholder

```
PASTE CONTENT FROM: workforce-showcase/docs/reports/REPO_EVALUATION_REPORT.md

Key questions to answer for this section:
- What is the purpose of this repo (dev showcase, documentation hub, marketing)?
- What backend API endpoints does it consume?
- What base URL does it use for API calls?
- What auth flow does it implement?
- What RBAC/permission checks does it perform?
- What CI/CD pipeline does it have?
- What is its deployment target domain?
- Are there cross-repo type/schema contracts?
```

### Workforce-Console Repo Report Placeholder

```
PASTE CONTENT FROM: workforce-console/docs/reports/REPO_EVALUATION_REPORT.md

Key questions to answer for this section:
- What is the purpose of this repo (admin console, ops dashboard)?
- What backend API endpoints does it consume?
- What base URL does it use for API calls?
- What auth flow does it implement?
- What RBAC/permission checks does it perform?
- What CI/CD pipeline does it have?
- What is its deployment target domain?
- Are there cross-repo type/schema contracts?
```

---

## Final Output Summary

1. **Cross-repo report path created:** `workforce-backup/docs/reports/WORKFORCE_CROSS_REPO_EVALUATION_REPORT.md`
2. **Repo reports available:** `workforce-backup` (direct clone access; no individual REPO_EVALUATION_REPORT.md exists yet)
3. **Repo reports missing / inaccessible:** `workforce-showcase` (404), `workforce-console` (404)
4. **Overall health rating:** 🟡 **Early Foundation (3/10)** — backend boots and tests pass; critical architecture decisions (RBAC schema, CORS, import roots) are unresolved; no CI; frontend-backend contract unconfirmed in production
5. **Top 5 blockers:**
   1. Dual RBAC schema — orphaned planned tables vs active biz_roles system
   2. CORS mismatch — frontend target domain not in backend allowlist
   3. workforce-showcase and workforce-console inaccessible — cross-repo compatibility unknown
   4. No CI/CD pipeline — regressions unguarded
   5. No production PostgreSQL migration path verified
6. **Top 5 next steps:**
   1. Reconcile dual RBAC schema and publish decision
   2. Fix CORS origin mismatch
   3. Access showcase and console repos; create individual REPO_EVALUATION_REPORT.md files
   4. Add GitHub Actions CI
   5. Cut Phase 0 foundation tag and begin Phase 1 formally
