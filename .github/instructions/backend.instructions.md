---
applyTo: "app/**/*.py"
---

# Backend Python Instructions

For files under `app/**/*.py`, follow these rules.

## Architecture
- Follow FastAPI + SQLAlchemy + Pydantic v2 conventions already used in the repository.
- Keep routers thin.
- Move business logic into service-layer functions or equivalent domain-oriented modules.
- Keep ORM concerns separate from API schema concerns.
- Reuse dependency injection patterns already present in the codebase.

## Multi-tenant and location-aware behavior
Assume all business operations may require scoping.

Always consider:
- `business_id`
- `location_id`
- role/permission context
- audit context

Do not write queries or service logic that can leak data across tenants or locations.

If an endpoint returns collections or detail records, verify that the current user is allowed to access that tenant/location scope.

## RBAC rules
- Enforce authorization explicitly.
- Prefer readable permission checks over hidden or magical behavior.
- Do not use convenience shortcuts that silently widen access.
- Treat permission checks as part of core feature implementation.

## Route handler rules
- Route handlers should orchestrate request parsing, auth dependency usage, service calls, and response formatting.
- Avoid placing complex validation logic and database logic directly in route handlers.
- Keep handlers concise and predictable.

## Service-layer rules
- Put business rules, orchestration, state transitions, and cross-entity workflows in service modules.
- Keep service functions cohesive and named for domain behavior.
- Validate important business invariants before persistence.

## Database access rules
- Keep query logic organized and reusable.
- Prefer clear filters over compact but opaque query code.
- Add eager loading or optimization only when it clearly improves behavior or avoids known issues.
- Maintain consistency with the project's async/sync database pattern already in use.

## Schema rules
- Use explicit request and response schemas.
- Prefer strong typing and clear field names.
- Do not expose internal-only fields unless intentionally required.
- Keep schema validation aligned with business rules.

## Model rules
When adding or modifying models, consider:
- tenant ownership
- location ownership
- lifecycle status
- audit timestamps
- foreign keys
- uniqueness constraints
- indexes

Avoid creating overlapping models for the same domain concept.

## Error handling
- Use clear, intentional HTTP errors where appropriate.
- Avoid swallowing exceptions silently.
- Preserve enough context for debugging without leaking sensitive implementation details.
- Prefer predictable API responses.

## Code style
- Use explicit types when practical.
- Prefer readability over cleverness.
- Add comments only when they help explain non-obvious intent.
- Avoid noisy or redundant comments.
- Follow existing naming conventions in the codebase.

## Tests
For meaningful backend changes:
- add or update focused tests
- cover happy path and failure path
- cover permission/scope behavior for tenant-aware features
- include edge cases for invalid input or missing records
