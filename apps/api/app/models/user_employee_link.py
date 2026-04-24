import os

if not os.environ.get('SKIP_WORKFORCE_MODELS'):
    try:
        from packages.workforce.workforce.app.models.user_employee_link import UserEmployeeLink  # noqa: F401
        __all__ = ["UserEmployeeLink"]
        _IMPORTED_CANONICAL = True
    except Exception:
        _IMPORTED_CANONICAL = False
else:
    _IMPORTED_CANONICAL = False

if not _IMPORTED_CANONICAL:
    from .user_employee_link_local import *  # noqa: F401,F403
