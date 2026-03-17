# Workforce repository instructions for GitHub Copilot

You are working in the Workforce monorepo.

## Mission
Build a recoverable, multi-tenant service-operations platform with a stable API core and widget-first UI.

## Foundation priorities
1. Respect tenant boundaries and location scoping.
2. Enforce permission checks consistently.
3. Preserve auditability and event emission on meaningful writes.
4. Prefer shared platform primitives over domain-specific duplication.
5. Keep changes small, reviewable, and reversible.

## Architecture rules
- Backend is API-first.
- Keep route handlers thin; use service-layer methods.
- Keep SQLAlchemy models explicit and readable.
- Use Alembic for all schema changes.
- Avoid silent breaking changes to request or response schemas.
- Emit audit and domain events for meaningful state changes.

## Multi-tenant rules
- Most business tables must carry `tenant_id`.
- Most operational tables should also carry `location_id`.
- Do not create features that assume a single tenant or single location.
- Access checks must combine actor, permission, and scope.

## UI rules
- Build the web app as a workspace shell with composable widgets.
- Do not hard-code large page-specific workflows when a reusable widget pattern fits.
- Navigation, filters, and widget visibility must be permission-aware.

## Change-control rules
When making meaningful changes:
- update relevant docs in `docs/`
- update `docs/TODO.md`
- update `docs/WORKLOG.md`
- update `docs/DECISIONS.md` if architecture or direction changes
- update `docs/CHANGELOG.md` if behavior changes
