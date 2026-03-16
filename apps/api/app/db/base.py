from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def import_models() -> None:
    """Import all models so Alembic metadata is populated.

    Prefer the full workforce models package when available — it imports every
    model module so SQLAlchemy metadata is complete.
    """
    # Import the consolidated models package (this will import every model module)
    import importlib

    try:
        pkg = importlib.import_module("apps.api.app.models")
        # Import every .py module inside the models package so SQLAlchemy metadata is populated.
        for p in pkg.__path__:
            try:
                for fn in sorted(os.listdir(p)):
                    if not fn.endswith(".py") or fn.startswith("__"):
                        continue
                    mod_name = fn[:-3]
                    try:
                        importlib.import_module(f"apps.api.app.models.{mod_name}")
                    except Exception:
                        # Import problems in one model should not prevent loading others.
                        # Log to stderr for debugging but continue.
                        import sys, traceback

                        traceback.print_exc(file=sys.stderr)
                        continue
            except FileNotFoundError:
                continue
    except Exception:
        # Fallback: import a small set of local models if the full package isn't present
        import apps.api.app.models.tenant  # noqa: F401
        import apps.api.app.models.user  # noqa: F401
        import apps.api.app.modules.hospitable.models.property_ops  # noqa: F401
