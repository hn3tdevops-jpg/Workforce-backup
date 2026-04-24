RBAC service implementation plan

This folder contains the RBAC service utilities. Current state:

- app.services.rbac_service: synchronous service functions that compute effective roles and permissions.

Next implementation steps (Phase 1):

1. Add async-friendly wrappers if needed for FastAPI dependency injection.
2. Add caching for permission lookups per-request.
3. Harden permission checks to cover explicit RolePermission -> Permission graph.
4. Add unit tests covering edge cases (no membership, inactive membership, multiple assignments).
5. Add integration tests to exercise endpoints with permission checks.

Small starter tasks:
- Create async wrapper: apps/api/app/services/async_rbac.py
- Add unit tests: tests/test_rbac_service_async.py
- Add todo tracking and begin implementing (this file)
