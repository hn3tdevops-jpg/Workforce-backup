# Prefer canonical identity models when available; fall back to local shims only on import failure
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
else:
    # Some canonical identity packages may omit ScopedRoleAssignment; ensure it's available
    try:
        ScopedRoleAssignment
    except NameError:
        from .access_control_local import ScopedRoleAssignment  # noqa: F401
        __all__ = globals().get("__all__", []) + ["ScopedRoleAssignment"]

# Ensure ScopedRoleAssignment present even if previous logic missed it
if 'ScopedRoleAssignment' not in globals():
    try:
        from .access_control_local import ScopedRoleAssignment as _ScopedRoleAssignment  # noqa: F401
        globals()['ScopedRoleAssignment'] = _ScopedRoleAssignment
        __all__ = globals().get("__all__", []) + ["ScopedRoleAssignment"]
    except Exception:
        pass
