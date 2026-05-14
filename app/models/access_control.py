# Top-level access control exports — prefer canonical packaged identity models.
# Fallback to local app modules when packaged models are unavailable.

try:
    from packages.workforce.workforce.app.models.identity import \
        BizRole as Role
    from packages.workforce.workforce.app.models.identity import \
        BizRolePermission as RolePermission
    from packages.workforce.workforce.app.models.identity import (
        Membership, MembershipLocationRole, MembershipRole, Permission,
        ScopedRoleAssignment)

    __all__ = [
        "Membership",
        "Role",
        "Permission",
        "RolePermission",
        "MembershipRole",
        "MembershipLocationRole",
        "ScopedRoleAssignment",
    ]
except Exception:
    try:
        from apps.api.app.models.access_control import *  # noqa: F401,F403
    except Exception:
        from apps.api.app.models.access_control_local import *  # noqa: F401,F403
