# Workforce agent operating rules

This repository is a multi-tenant service-operations platform.

## Always optimize for
- recoverability
- tenant safety
- scope-aware access control
- small reviewable changes
- clear project-control updates

## Required workflow
1. Inspect the existing code pattern before changing architecture.
2. Describe the intended change in concrete terms.
3. Make the smallest useful implementation.
4. Run the relevant validation available in the repo.
5. Update project-control docs for meaningful work.

## Required project-control updates
When work is meaningful, update as applicable:
- `docs/TODO.md`
- `docs/WORKLOG.md`
- `docs/DECISIONS.md`
- `docs/CHANGELOG.md`
- `docs/PHASE_STATUS.md`

## Architecture priorities
1. tenant / business / location core
2. RBAC with scope-aware permission checks
3. shared workforce/time/scheduling modules
4. shared communications, tasks, and inventory modules
5. widget-first workspaces
6. domain-specific packs on top of shared primitives

## Do not do casually
- change schema shape without migration planning
- hard-code single-tenant assumptions
- bypass permission-aware access patterns
- add page-specific UI when a reusable widget fits
- leave docs stale after structural changes
