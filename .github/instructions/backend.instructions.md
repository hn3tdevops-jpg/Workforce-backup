# Backend instructions

Apply these instructions when working on backend, API, database, permissions, services, migrations, tests, or integrations.

## Backend standards
- Use FastAPI, SQLAlchemy 2.x, Alembic, and Pydantic v2 patterns consistently.
- Keep API schemas explicit.
- Keep service logic outside route handlers.
- Use dependency injection for auth context, DB session, and scoped access where appropriate.

## Data discipline
- Prefer explicit tables over premature generic abstraction.
- Use shared base columns and naming conventions.
- Never bypass Alembic for schema evolution.
- Treat audit and domain events as first-class concerns.

## RBAC discipline
- Roles are bundles.
- Permissions are atomic.
- Enforcement must be scope-aware.
- Check tenant and location scope before reads and writes.

## Testing priorities
Prioritize tests for:
- permission enforcement
- tenant isolation
- schedule/time logic
- inventory movement correctness
- state transition logic
- migration safety for critical schema changes
