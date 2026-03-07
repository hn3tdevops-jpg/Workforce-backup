---
applyTo: "tests/**/*.py"
---

# Test Instructions

- Prefer focused tests over broad brittle tests.
- Cover happy path, failure path, and permission/scope behavior.
- Add tenant and location isolation tests for scoped features.
- Keep fixtures minimal and reusable.
- Avoid testing private implementation details when public behavior can be tested instead.