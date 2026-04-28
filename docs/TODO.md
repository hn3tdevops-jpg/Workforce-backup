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
