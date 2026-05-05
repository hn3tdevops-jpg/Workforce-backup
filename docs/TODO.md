# TODO

## Current phase
Phase 0 — Foundation Freeze

## Now
- [ ] Copy repo-base scaffold into the Workforce repo
- [ ] Commit project-control files
- [ ] Confirm Python runtime target
- [ ] Confirm monorepo directory layout
- [x] Verify app still boots after docs-only change
- [x] Document register vs invite behavior (2026-04-27)
- [x] Audit canonical RBAC model and document in DECISIONS.md (D-0011) (2026-05-03)
- [x] Fix CORS allowlist — add Render frontend origin (2026-05-03)
- [x] Fix CI workflow — PYTHONPATH, SKIP_WORKFORCE_MODELS, correct matrix (2026-05-03)
- [x] Add `GET /api/v1/auth/me/access-context` backend endpoint (COMPAT scope from RBAC) (2026-05-05)
- [ ] Verify Alembic migration chain on PostgreSQL before cutting foundation-v0.1 tag
- [ ] Create `foundation-v0.1` tag

## Next
- [ ] Inventory current models and migrations
- [ ] Define tenant/business/location schema
- [ ] Define memberships and scoped role assignments
- [ ] Define atomic permission catalog
- [x] Add permission-resolution helpers
- [ ] Add audit/event tables
- [ ] Run broader backend test suite
- [ ] Confirm deployment entrypoint uses the updated `SKIP_WORKFORCE_MODELS=1` boot path

## Later
- [ ] Build workforce/time core
- [ ] Build communications core
- [ ] Build inventory core
- [ ] Build widget workspace shell
- [ ] Add first domain pack
