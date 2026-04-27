# Try to reuse canonical Business/Location; Tenant remains local when canonical present.
from apps.api.app.core.imports import skip_canonical_models, record_model_import

# Diagnostic record
try:
    record_model_import(__name__)
except Exception:
    pass

if not skip_canonical_models():
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
