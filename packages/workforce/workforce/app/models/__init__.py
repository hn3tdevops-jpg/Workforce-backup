# Package models registry.
# Avoid importing all model modules eagerly here; importing this package should not
# automatically populate SQLAlchemy metadata to prevent duplicate Table registration
# when the same model classes are available through different import paths.
__all__ = [
    "base",
    "business",
    "employee",
    "scheduling",
    "training",
    "audit",
    "identity",
    "auth",
    "timeclock",
    "marketplace",
    "schedule",
    "dashboard",
    "messaging",
    "hkops",
]

# Ensure scheduling models are importable under the package name so that
# SQLAlchemy relationships referencing 'models.scheduling.AvailabilityBlock'
# can be resolved even when models are discovered via different import paths.
# Importing this module is intentionally lightweight: it only imports model
# definitions (no side-effects) and makes them available as
# 'packages.workforce.workforce.app.models.scheduling'.
from . import employee  # noqa: F401  # ensure Employee is registered before scheduling
from . import scheduling  # noqa: F401
from . import identity  # noqa: F401  # ensure identity models (User, Membership) are registered
