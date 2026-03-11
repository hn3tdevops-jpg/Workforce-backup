# RBAC IMPLEMENTATION AUDIT — FILE INDEX

## Overview

This directory contains a comprehensive audit of the Workforce platform's RBAC (Role-Based Access Control) implementation, comparing it against the requirements in `HN3T_MASTER_PLAN.md` Sections 3 & 4.

---

## Audit Documents

### 1. **RBAC_IMPLEMENTATION_AUDIT.md** (MAIN REPORT)
   - **Length**: ~775 lines
   - **Contents**:
     - Executive summary
     - All existing tables & models (both active and orphaned)
     - RBAC enforcement mechanism in auth_deps.py
     - Location owner delegation status (gaps identified)
     - Job title display implementation
     - Effective permissions API status
     - Audit logging coverage
     - Data structure comparison vs. master plan
     - Route/endpoint summary
     - Detailed gaps analysis
     - Code quality observations
     - Recommendations (high/medium/low priority)
     - Schema diagram
     - Final assessment scorecard

### 2. **RBAC_SUMMARY.txt** (QUICK REFERENCE)
   - **Length**: ~120 lines
   - **Format**: Text with ASCII tables and checkmarks
   - **Contents**:
     - Active RBAC models list with ✅/❌ status
     - Orphaned tables (never used)
     - Master plan requirements matrix
     - Key files by category
     - Authorization rule summary
     - RBAC endpoints list
     - Permission examples
     - Default roles
     - Gaps summary
     - Next steps checklist

### 3. **RBAC_CODE_SNIPPETS.md** (DEVELOPER REFERENCE)
   - **Length**: ~400 lines
   - **Contents**:
     - Complete code listings for:
       - Core RBAC models (Permission, BizRole, MembershipLocationRole)
       - Permission checking functions (_get_user_permissions, _get_user_location_permissions)
       - require_permission() dependency
       - Job title derivation function
       - Location role assignment endpoint
       - Permission & role seeding
       - Key migration changes
     - Inline comments highlighting master plan compliance

---

## Key Findings Summary

### ✅ What's Implemented

```
Core RBAC Models:
  ✅ Permission (unique keys)
  ✅ BizRole (with scope_type, location_id, priority)
  ✅ BizRolePermission (role-permission links)
  ✅ Membership (user-business binding)
  ✅ MembershipRole (business-scoped assignments)
  ✅ MembershipLocationRole (location-scoped assignments)
  ✅ AuditEvent (infrastructure for logging)

Master Plan Fields:
  ✅ scope_type on roles (BUSINESS | LOCATION)
  ✅ location_id on roles (for location scoping)
  ✅ priority on roles (for job title selection)
  ✅ job_title_label on assignments (display override)
  ✅ created_by_user_id on assignments (change tracking)

Authorization:
  ✅ RBAC enforcement at route level
  ✅ Location-scoped permission checks
  ✅ Superadmin bypass
  ✅ Permission union (business + location)

Job Title:
  ✅ Display-only (never used for auth)
  ✅ Priority-based selection
  ✅ Custom label support
```

### ❌ What's Missing

```
Critical Gaps:
  ❌ Location owner delegation (rbac.location_roles.manage)
  ❌ Location assignment delegation (rbac.location_assignments.manage)
  ❌ Audit logging for RBAC changes (not written to AuditEvent)
  ❌ Effective permissions API endpoint

Important Gaps:
  ⚠️ Orphaned tables (roles, role_permissions, user_role_assignments)
  ⚠️ Generic "roles:write" instead of location-specific perms
  ⚠️ No guard to prevent removing last location owner
  ⚠️ Permission naming doesn't match master plan format
```

---

## File Locations (Source Code)

### Models
- `/app/models/identity.py` — BizRole, MembershipRole, MembershipLocationRole, Permission, AuditEvent
- `/app/models/business.py` — Business, Location (tenant scoping)

### RBAC Enforcement
- `/app/core/auth_deps.py` — All permission checking logic
- `/app/core/permissions.py` — Legacy helper (minimal)

### Routes/Endpoints
- `/api/v1/tenant/routes.py` — RBAC management endpoints
- `/api/v1/control/routes.py` — SuperAdmin + system roles

### Seeds/Services
- `/app/services/roles_seed.py` — DEFAULT_PERMISSIONS, DEFAULT_ROLES, seed functions
- `/app/cli/seed_rbac.py` — CLI command

### Database Migrations
- `alembic/versions/fff13ba5ecee_identity_rbac_agents.py` — Initial RBAC tables
- `alembic/versions/b7c2e4f1a9d3_per_location_rbac.py` — Add scope_type, location_id, priority
- `alembic/versions/zz_add_rbac_tables.py` — Orphaned tables (unused)

---

## How to Use This Audit

### For Quick Understanding
1. Read **RBAC_SUMMARY.txt** (2-5 min)
2. Check the **Master Plan Requirements** table
3. Review **Next Steps** checklist

### For Implementation
1. Read **RBAC_IMPLEMENTATION_AUDIT.md** Section 9 (Gaps)
2. Read **RBAC_IMPLEMENTATION_AUDIT.md** Section 11 (Recommendations)
3. Reference code in **RBAC_CODE_SNIPPETS.md** for implementation patterns

### For Code Review
1. Reference **RBAC_CODE_SNIPPETS.md** for exact implementations
2. Check **RBAC_IMPLEMENTATION_AUDIT.md** Section 2 for enforcement logic
3. Verify against **RBAC_IMPLEMENTATION_AUDIT.md** Section 8 for endpoints

### For Architecture Discussion
1. Read **RBAC_IMPLEMENTATION_AUDIT.md** Section 7 (Data Structure Comparison)
2. Review **RBAC_IMPLEMENTATION_AUDIT.md** Section 12 (Schema Diagram)
3. Discuss Sections 9 & 11 (Gaps & Recommendations)

---

## Master Plan References

### HN3T_MASTER_PLAN.md Sections Covered

**Section 3 — Per-Location RBAC Model**
- ✅ IMPLEMENTED: scope_type, location_id, priority, job_title_label, created_by_user_id
- ✅ IMPLEMENTED: Authorization rule with location scoping
- ✅ IMPLEMENTED: Per-location assignments via MembershipLocationRole

**Section 4 — Location Owner Delegated Management**
- ❌ MISSING: rbac.location_roles.manage permission
- ❌ MISSING: rbac.location_assignments.manage permission
- ❌ MISSING: Location-owner-only checks on role/assignment endpoints

**Section 5 — Profile Page / Job Title Display**
- ✅ IMPLEMENTED: Job title purely display-based
- ✅ IMPLEMENTED: Priority-based selection
- ✅ IMPLEMENTED: Custom label support via job_title_label

**Section 6 — Effective Permissions Computation**
- ⚠️ PARTIAL: Logic exists but not exposed via API endpoint

---

## Assessment Scorecard

| Criterion | Score | Notes |
|-----------|-------|-------|
| Per-location RBAC | ✅ 95% | Locations scoped, but missing delegation guards |
| Job title display | ✅ 100% | Correctly prioritized and display-only |
| Permission enforcement | ✅ 90% | Enforced at all endpoints, missing location-owner checks |
| Audit logging | ❌ 20% | Infrastructure exists, not used for RBAC |
| API completeness | ⚠️ 70% | Missing effective permissions endpoint |
| Code quality | ✅ 85% | Good types/DI, but orphaned tables confuse design |
| Master plan adherence | ⚠️ 75% | All fields exist, different model structure |
| **OVERALL** | **⚠️ 80%** | **Functionally complete, missing delegation & audit** |

---

## Next Action Items

### CRITICAL (Do First)
- [ ] Implement location-owner delegation checks
- [ ] Add audit logging for RBAC changes
- [ ] Create effective permissions API endpoint

### IMPORTANT (Do Next)
- [ ] Add permission naming standards
- [ ] Cleanup orphaned tables
- [ ] Add last-location-owner guard
- [ ] Add database constraints for scope_type/location_id

### NICE-TO-HAVE (Later)
- [ ] Documentation of permission matrix
- [ ] Test coverage for location-scoped RBAC
- [ ] Cache permission lookups

---

## Questions & Clarifications

### Q: Why are there two sets of RBAC tables?
**A:** The original master plan tables (roles, role_permissions, user_role_assignments) were created in migration `zz_add_rbac_tables` but never used. Instead, the active system uses BizRole + Membership + MembershipRole/LocationRole. This may have been a design iteration.

### Q: Are the master plan fields actually used?
**A:** Yes. `scope_type`, `location_id`, and `priority` are actively populated and used in BizRole. `job_title_label` and `created_by_user_id` are set when creating assignments. The authorization rule correctly checks scope and location.

### Q: What's the impact of missing location-owner delegation?
**A:** Currently, any user with `roles:write` permission in a business can assign roles at ANY location. The master plan intended only location owners to manage their location's roles. This is a **security/design gap**.

### Q: Is the audit trail completely missing?
**A:** No. The AuditEvent table exists and is used in control plane endpoints. But it's NOT being written to for RBAC changes (role creation, permission assignment, member role assignments). This is a **compliance gap**.

---

## Contact & Updates

Generated: 2026-03-07
Last Updated: Based on latest codebase
Audit Scope: Workforce platform, /app directory, RBAC models + routes

For questions or updates to this audit, refer to the full documents listed above.

