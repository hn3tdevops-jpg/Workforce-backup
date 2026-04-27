"""Centralized import-guard helpers for canonical packages.workforce imports.

Provide a single place to opt-out of importing the canonical packaged models
(e.g., during test collection) and to import the canonical model modules when
desired.
"""
import os
import importlib


import traceback


def skip_canonical_models() -> bool:
    return bool(os.environ.get("SKIP_WORKFORCE_MODELS"))


# Diagnostic flags tracking import progress
IMPORTS_DONE = False
IMPORTS_IN_PROGRESS = False


def record_model_import(module_name: str) -> None:
    """Record a model module import for diagnostics if imports not yet completed.

    Writes a small diagnostic record to /tmp/model_imports.log when a model
    module is imported before import_models() is started. This helps detect
    import-order races that produce SQLAlchemy metadata conflicts.
    """
    try:
        # Only log imports that occur before import_models begins.
        if not IMPORTS_DONE and not IMPORTS_IN_PROGRESS:
            with open("/tmp/model_imports.log", "a") as f:
                f.write(f"EARLY_IMPORT {module_name}\n")
                f.write(''.join(traceback.format_stack()))
                f.write("\n")
    except Exception:
        # Best-effort, do not fail import path
        pass


def import_models(*_args, **_kwargs) -> None:
    """Import canonical or local model modules depending on opt-out.

    If SKIP_WORKFORCE_MODELS is set, import the local apps.api.app.models modules
    so tests register model tables under the apps.api.app package. Otherwise
    prefer to import the canonical packages.workforce set.
    """
    global IMPORTS_IN_PROGRESS, IMPORTS_DONE
    IMPORTS_IN_PROGRESS = True

    if skip_canonical_models():
        # Import the local app model modules
        try:
            importlib.import_module("apps.api.app.models.base")
            importlib.import_module("apps.api.app.models.tenant")
            # Import user model before access_control to ensure users.business_id FK
            # references the businesses table already present in metadata.
            importlib.import_module("apps.api.app.models.user")
            importlib.import_module("apps.api.app.models.access_control")
        except Exception:
            # Best-effort; callers may handle import errors
            IMPORTS_IN_PROGRESS = False
            return

    # Mark diagnostics flag after successful local import
    IMPORTS_DONE = True
    IMPORTS_IN_PROGRESS = False

    # Not skipping canonical models: prefer canonical packaged models
    try:
        importlib.import_module("packages.workforce.workforce.app.models")
    except Exception:
        # Fall back to local models if canonical import fails
        try:
            importlib.import_module("apps.api.app.models.base")
            importlib.import_module("apps.api.app.models.tenant")
            # Import user entry before access_control so FK string references
            # can resolve reliably during metadata processing.
            importlib.import_module("apps.api.app.models.user")
            importlib.import_module("apps.api.app.models.access_control")
        except Exception:
            return
