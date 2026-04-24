import os

if not os.environ.get('SKIP_WORKFORCE_MODELS'):
    try:
        from packages.workforce.workforce.app.models.identity import (
            Membership,
            BizRole as Role,
            Permission,
            BizRolePermission as RolePermission,
            MembershipRole,
            MembershipLocationRole,
            ScopedRoleAssignment,
        )
        __all__ = [
            "Membership",
            "Role",
            "Permission",
            "RolePermission",
            "MembershipRole",
            "MembershipLocationRole",
            "ScopedRoleAssignment",
        ]
        _IMPORTED_CANONICAL = True
    except Exception:
        _IMPORTED_CANONICAL = False
else:
    _IMPORTED_CANONICAL = False

if not _IMPORTED_CANONICAL:
    from .access_control_local import *  # noqa: F401,F403
