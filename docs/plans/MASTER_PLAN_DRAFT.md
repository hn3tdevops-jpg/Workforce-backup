# Master Plan — Draft

This draft consolidates immediate, actionable work items derived from the canonical HN3T master plan (docs/plans/HN3T_MASTER_PLAN.md). It is intended to be reviewed and iterated quickly in small, reversible changes.

Phases (summary)

- Phase 0: Apply & bootstrap — environment, secrets, and initial data (Business, Location, Admin user).
- Phase 1: Multi-tenant scaffold — tenancy model, tenant-scoped tables, and baseline RBAC.
- Phase 2: Auth & RBAC — role model, permission catalog, assignment APIs, location-scoped enforcement.
- Phase 3: Core operations — employees, scheduling, shifts, tasks, and widget-driven UI.
- Phase 4: Integrations & agents — API keys, agent plane, least-privilege integrations, and observability.

Milestones (first pass)

1. Stabilize tenancy core: ensure tenant_id and optional location_id on business tables; add tests for isolation.
2. Finalize per-location RBAC schema and enforcement in service layer; add migration notes.
3. Implement minimal API surface for employee management and scheduling widgets.
4. Provide migration and rollout plan; run canary migration against a staging DB.

Immediate next tasks

- Create review branch and add this draft (this commit).
- Solicit 2 reviewers and collect feedback within one week.
- Reconcile duplicate master-plan files and add links in docs index.

Constraints & rules

- Use Alembic for ALL schema changes.
- Keep route handlers thin; use service-layer implementations.
- Emit audit events on meaningful writes.

Reference: docs/plans/HN3T_MASTER_PLAN.md
