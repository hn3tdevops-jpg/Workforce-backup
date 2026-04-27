# Try to reuse canonical Business/Location; Tenant remains local when canonical present.
import os

# Honor test harness opt-out: don't import packages.workforce when SKIP_WORKFORCE_MODELS is set
if not os.environ.get('SKIP_WORKFORCE_MODELS'):
    try:
        from packages.workforce.workforce.app.models.business import Business, Location  # noqa: F401
        from .tenant_local import Tenant  # Tenant kept local currently
        __all__ = ["Tenant", "Business", "Location"]
        _IMPORTED_CANONICAL = True
    except Exception:
        _IMPORTED_CANONICAL = False
else:
    _IMPORTED_CANONICAL = False

if not _IMPORTED_CANONICAL:
    from .tenant_local import *  # noqa: F401,F403
