# HN3T Workforce / Hospitable Ops — Copilot Instructions

## Project identity
This repository implements the HN3T Workforce / Hospitable Ops platform.

Use `HN3T_MASTER_PLAN.md` as the primary implementation roadmap, feature priority source, and architectural intent document.

When a request is ambiguous, align decisions with:
1. `HN3T_MASTER_PLAN.md`
2. existing repository patterns
3. production-safe incremental delivery

## Core stack
Assume and preserve this architecture unless explicitly told otherwise:

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic v2
- Async-first backend patterns where already in use

## General implementation rules
- Make small, safe, reviewable changes.
- Prefer extending existing modules over creating duplicate systems.
- Before creating a new model, router, schema, service, or utility, inspect the repository for an existing pattern to follow.
- Keep changes incremental and production-minded.
- Favor maintainable, copy-paste-ready code over placeholders.
- Avoid TODO-heavy scaffolding unless explicitly requested.
- Preserve existing behavior unless the task explicitly requires refactoring or redesign.

## Source of truth behavior
When implementing a feature:
- identify the relevant section of `HN3T_MASTER_PLAN.md`
- align naming, structure, and scope with that section
- avoid inventing architecture that conflicts with the master plan

If the repository already contains a stable pattern that differs slightly from the plan, prefer adapting carefully instead of forcing a disruptive rewrite.

## Domain rules
This system is multi-tenant and location-aware.

Always assume:
- business scoping matters
- location scoping matters
- role/permission scoping matters
- auditability matters

Never generate code that casually bypasses tenant boundaries.

### Required scoping mindset
- Respect `business_id` boundaries where applicable.
- Respect `location_id` boundaries where applicable.
- RBAC is location-scoped unless explicitly documented otherwise.
- Do not expose cross-tenant or cross-location data without an intentional authorization path.
- Queries, services, and endpoints must enforce scope consistently.

## RBAC and authorization rules
- Treat authorization as core behavior, not optional polish.
- Enforce access checks in the proper layer.
- Do not hardcode broad admin bypasses for convenience.
- Prefer explicit permission checks over implicit assumptions.
- If a feature affects users, roles, assignments, schedules, housekeeping, inspections, inventory, or reporting, consider tenant scope and permission scope together.

## Backend architecture rules
Favor separation of concerns:

- routers: HTTP concerns only
- schemas: request/response validation and serialization
- services: business logic and orchestration
- repositories/data access: database querying and persistence
- models: ORM definitions only

Keep route handlers thin.
Do not bury complex business logic in API endpoint functions.

## Data modeling rules
- Prefer normalized schema design unless denormalization is justified.
- Use Alembic migrations for schema changes.
- Do not rely on manual database edits as part of the intended implementation.
- Add foreign keys, indexes, uniqueness constraints, and status fields deliberately.
- Include `created_at` / `updated_at` style fields where appropriate.
- Include ownership/scope fields where the domain requires them.
- Avoid destructive migrations unless explicitly requested.
- Avoid duplicate concepts with slightly different names.

Before adding a new table or model, consider:
- tenant ownership
- location ownership
- status lifecycle
- audit fields
- foreign keys
- query patterns
- reporting implications

## API conventions
- Keep endpoints resource-oriented and predictable.
- Use explicit Pydantic v2 request and response schemas.
- Return consistent error structures.
- Add pagination and filtering to list endpoints when datasets can grow.
- Validate user input thoroughly.
- Favor clear naming over abbreviations.

## Frontend / UI guidance
When frontend or template work is requested:
- preserve dark-theme support
- keep navigation grouped by domain
- keep business/location context visible when relevant
- prefer reusable components over repeated markup
- avoid cluttered layouts
- keep role-sensitive actions clearly separated

Preferred high-level navigation grouping:
- Workforce
- Housekeeping
- Inspections
- Inventory
- Maintenance
- Admin
- Reports

## Integration guidance
This platform may integrate with an existing scheduling / timeclock / workforce system.

When implementing integrations:
- preserve separation of concerns
- do not duplicate source-of-truth domains unnecessarily
- document assumptions about ownership of employee, schedule, and timeclock data
- prefer stable interfaces over tightly coupled shortcuts

## Testing expectations
- Add or update tests for non-trivial changes.
- Test happy path, failure path, and permission/scope behavior.
- Include edge cases for invalid input, missing resources, and unauthorized access.
- Verify tenant isolation and location isolation in tests where relevant.
- Prefer focused tests over broad fragile tests.

## Quality bar
Generated code should be:
- explicit
- typed where appropriate
- readable
- consistent with project patterns
- safe for incremental production development

## Avoid
- Do not hardcode secrets, tokens, credentials, or environment-specific values.
- Do not bypass RBAC, tenant scoping, or location scoping for convenience.
- Do not create parallel architectures for the same domain concept.
- Do not introduce a new framework or major dependency unless requested.
- Do not make broad speculative rewrites when the user asked for a focused change.

## Preferred response behavior for coding tasks
When asked to implement or modify something:
- first inspect surrounding code patterns
- align work to `HN3T_MASTER_PLAN.md`
- make the smallest complete change that solves the problem
- include supporting tests when appropriate
- keep naming and structure consistent with the repository
