"""Shim to re-export DB helpers from the workforce package.
This ensures imports like `from apps.api.app.core.db import get_db` work regardless of package layout.
When tests set SKIP_WORKFORCE_MODELS=1 this module avoids importing the packages.workforce
modules to prevent duplicate SQLAlchemy model registration during test collection.
"""
import os

if not os.environ.get("SKIP_WORKFORCE_MODELS"):
    from packages.workforce.workforce.app.core.db import *  # noqa: F401,F403
else:
    # Test mode: provide a minimal placeholder to avoid import-time side-effects.
    # Tests should override DB dependencies (e.g., get_async_session) as needed.
    def get_db():
        raise RuntimeError("packages.workforce models are skipped in test mode; DB helper unavailable")
