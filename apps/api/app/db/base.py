from apps.api.app.core.imports import import_models  # re-export central import helper

# Backwards-compatible alias expected by some tests
def import_core_models(*args, **kwargs):
    return import_models(*args, **kwargs)

# Re-export Base from models.base so callers like tests/conftest.py can import Base
from apps.api.app.models.base import Base  # type: ignore

# Ensure sqlite accepts Python uuid.UUID objects by registering an adapter early
# This makes tests that construct model instances with uuid.UUID work with the
# in-memory sqlite driver used by the test harness.
try:
    import sqlite3
    import uuid as _uuid_module
    sqlite3.register_adapter(_uuid_module.UUID, lambda u: str(u))
except Exception:
    # Not critical; if sqlite isn't available or registration fails, continue.
    pass
