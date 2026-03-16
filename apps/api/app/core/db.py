"""Shim to re-export DB helpers from the workforce package.
This ensures imports like `from apps.api.app.core.db import get_db` work regardless of package layout.
"""
from packages.workforce.workforce.app.core.db import *  # noqa: F401,F403
