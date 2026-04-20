import os

if not os.environ.get('SKIP_WORKFORCE_MODELS'):
    try:
        from packages.workforce.workforce.app.models.employee import Employee as EmployeeProfile
        __all__ = ["EmployeeProfile"]
        _IMPORTED_CANONICAL = True
    except Exception:
        _IMPORTED_CANONICAL = False
else:
    _IMPORTED_CANONICAL = False

if not _IMPORTED_CANONICAL:
    from .employee_local import *  # noqa: F401,F403
