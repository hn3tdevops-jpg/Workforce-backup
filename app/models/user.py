# Re-export user model (explicit)
from apps.api.app.models.user import User  # noqa: F401
__all__ = ["User"]
