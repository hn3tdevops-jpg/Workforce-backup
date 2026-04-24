# Re-export shim to ensure imports using app.models.access_control_local
# resolve to the canonical implementation in apps.api.app.models.
# This avoids mixed package imports between `app.*` and `apps.api.app.*`.
try:
    from apps.api.app.models.access_control_local import *  # noqa: F401,F403
except Exception:
    # As a fallback, try to import from the canonical packaged identity
    # implementation if available.
    try:
        from packages.workforce.workforce.app.models.identity import *  # noqa: F401,F403
    except Exception:
        # If neither is available, leave the module empty; importing
        # modules that expect these names will raise a clear error.
        pass
