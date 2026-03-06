# AGENTS.md

## Mission
Implement the HN3T Workforce / Hospitable Ops platform safely and incrementally, using `HN3T_MASTER_PLAN.md` as the primary roadmap.

## Primary planning source
Before making architectural or feature decisions, read and align with:
- `HN3T_MASTER_PLAN.md`

Also inspect nearby existing code before introducing new patterns.

## Operating mode
- Prefer small, reviewable, production-safe changes.
- Implement one complete feature slice at a time when possible.
- Reuse existing patterns, modules, and naming conventions.
- Avoid speculative redesigns unless explicitly requested.

## Execution priorities
Prioritize work in this order:
1. correctness
2. tenant and location safety
3. RBAC integrity
4. maintainability
5. consistency with repository patterns
6. speed

## Mandatory safety rules
- Never weaken tenant isolation.
- Never weaken location scoping.
- Never bypass RBAC for convenience.
- Never hardcode secrets or credentials.
- Never replace stable architecture with a new framework unless explicitly requested.
- Never make destructive schema changes unless explicitly requested.

## Implementation behavior
When asked to build or change something:
1. inspect the relevant files first
2. map the request to the relevant section of `HN3T_MASTER_PLAN.md`
3. implement the smallest complete change that solves the task
4. update tests when appropriate
5. keep code easy to review

## Backend expectations
- Keep API route handlers thin.
- Put business logic into services or equivalent domain modules.
- Use Pydantic v2 schemas explicitly.
- Use Alembic for schema changes.
- Respect SQLAlchemy and FastAPI patterns already present in the repo.

## Database and migration rules
- Treat schema work as production-grade work.
- Preserve data integrity with constraints and indexes where appropriate.
- Consider ownership, lifecycle, and auditability for every new entity.
- Avoid duplicate tables or near-duplicate concepts.

## Scope awareness
For features involving users, employees, schedules, housekeeping, inspections, inventory, rooms, maintenance, vendors, reporting, or admin:
- verify tenant scope
- verify location scope
- verify permission scope
- verify audit implications

## Testing expectations
For non-trivial changes:
- add or update tests
- cover at least one success case
- cover at least one failure or authorization case
- verify scope isolation where relevant

## Output expectations
After making changes, summarize:
- what changed
- which files changed
- any important assumptions
- any follow-up work still needed