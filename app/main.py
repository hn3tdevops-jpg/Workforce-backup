# Compatibility shim: re-export the FastAPI app object
from apps.api.app.main import app as app
__all__ = ("app",)
