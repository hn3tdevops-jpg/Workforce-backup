import os

# Load local definitions first as a safe baseline; allow canonical identity to
# override any names that are present there.
try:
    from .access_control_local import *  # noqa: F401,F403
except Exception:
    # If local fallback isn't available, continue and attempt canonical imports.
    pass

# Attempt to import canonical identity models and override local names when present.
_IMPORTED_CANONICAL = False
if not os.environ.get('SKIP_WORKFORCE_MODELS'):
    try:
        from packages.workforce.workforce.app.models.identity import (
            Membership as CanonicalMembership,
            BizRole as CanonicalRole,
            Permission as CanonicalPermission,
            BizRolePermission as CanonicalRolePermission,
            MembershipRole as CanonicalMembershipRole,
            MembershipLocationRole as CanonicalMembershipLocationRole,
            ScopedRoleAssignment as CanonicalScopedRoleAssignment,
        )
        # Override local aliases with canonical implementations where available
        Membership = CanonicalMembership
        Role = CanonicalRole
        Permission = CanonicalPermission
        RolePermission = CanonicalRolePermission
        MembershipRole = CanonicalMembershipRole
        MembershipLocationRole = CanonicalMembershipLocationRole
        if CanonicalScopedRoleAssignment is not None:
            ScopedRoleAssignment = CanonicalScopedRoleAssignment

        _IMPORTED_CANONICAL = True
    except Exception:
        _IMPORTED_CANONICAL = False

# Build __all__ based on what is actually present in the module namespace.
__all__ = [
    "Membership",
    "Role",
    "Permission",
    "RolePermission",
    "MembershipRole",
    "MembershipLocationRole",
]
if "ScopedRoleAssignment" in globals():
    __all__.append("ScopedRoleAssignment")
