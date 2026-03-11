import sys
import os
import asyncio

project_home = os.path.abspath(os.path.dirname(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from dotenv import load_dotenv  # noqa: E402
# Load .env from project root; allow override via WORKFORCE_PROJECT_HOME if needed
env_path = os.environ.get("WORKFORCE_PROJECT_HOME", os.path.join(project_home, '.env'))
load_dotenv(env_path)
# Ensure required env vars for PythonAnywhere deployment
os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL", "sqlite:////home/hn3t/workforce/dev.db")
os.environ["ENV"] = os.environ.get("ENV", "prod")
os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY", "Eq4zr-S23gs2ngGtIyCwtoB3nUCbsh9jJ6OoVfvb4ikFPoglJk2TNOsrp1EO8vf_iZCwZm5fIloMMBy28ujwpQ")

from a2wsgi import ASGIMiddleware  # noqa: E402

# Lazy ASGI->WSGI bridge: avoid importing the ASGI app at module import time
_app = None

def application(environ, start_response):
    global _app
    if _app is None:
        # Import the ASGI app lazily and wrap it with a2wsgi's ASGIMiddleware
        from apps.api.app.main import app as asgi_app  # noqa: E402
        _app = ASGIMiddleware(asgi_app)
    return _app(environ, start_response)
