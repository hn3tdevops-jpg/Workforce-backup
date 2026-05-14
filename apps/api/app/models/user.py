# Prefer canonical packaged User model when available; fallback to local shim on import error
import os
from apps.api.app.core.imports import record_model_import

# Record that user model module imported (for diagnostics)
try:
    record_model_import(__name__)
except Exception:
    pass

if not os.environ.get('SKIP_WORKFORCE_MODELS'):
    try:
        from packages.workforce.workforce.app.models.identity import User  # noqa: F401
        __all__ = ["User"]
        _IMPORTED_CANONICAL = True
    except Exception:
        _IMPORTED_CANONICAL = False
else:
    _IMPORTED_CANONICAL = False

if not _IMPORTED_CANONICAL:
    from .user_local import *  # noqa: F401,F403
