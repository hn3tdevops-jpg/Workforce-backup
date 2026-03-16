# Phase 1 — Tenancy checklist

- [ ] Review HN3T_MASTER_PLAN.md Phase 1 Tenancy section
- [ ] Review docs/rbac and RBAC_AUDIT_INDEX.md
- [ ] Add tenancy models (Tenant, Membership) and migrations
- [ ] Integrate membership-based RBAC queries in app/core/permissions.py
- [ ] Add DB migration and apply to dev.db
- [ ] Add unit tests for tenancy and permission checks
- [ ] Run tests, fix failures, update CI if needed
- [ ] Open PR from branch 'phase1-tenancy' and link to progress report

## Design notes (summary)

- Use existing Business + Location models as the tenancy boundary; do NOT create a duplicate "Tenant" table unless multi-business grouping is required.
- Membership already exists (Membership, MembershipRole, MembershipLocationRole). Ensure membership is the canonical user-to-business binding and that location-scoped assignments use MembershipLocationRole.
- Enforce location-owner delegation: add permission checks so only users with `rbac.location_roles.manage` or explicit Location Owner can manage roles/assignments at that location.
- Audit RBAC changes: write AuditEvent entries for role creation/assignment/removal.
- Add Effective Permissions API: endpoint to return computed permissions for a user at a business/location (cacheable, but include invalidation hooks).
- DB: add constraints for scope_type/location_id and a guard to prevent removing last location owner. Add migrations and indexes for permission lookups.
- Tests: unit tests for membership joins, location-owner delegation, last-owner guard, and effective-permissions computation.
- Next immediate step: review RBAC_AUDIT_INDEX.md 'Critical' items and implement location-owner delegation + audit logging first.
