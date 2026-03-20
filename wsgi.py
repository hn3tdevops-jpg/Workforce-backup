import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
API_ROOT = os.path.join(PROJECT_ROOT, "apps", "api")

# Make canonical backend win import resolution
for path in [API_ROOT, PROJECT_ROOT]:
    if path in sys.path:
        sys.path.remove(path)
    sys.path.insert(0, path)

from dotenv import load_dotenv

env_path = os.environ.get("WORKFORCE_ENV_FILE", os.path.join(PROJECT_ROOT, ".env"))
load_dotenv(env_path)

os.environ.setdefault("APP_ENV", "prod")
os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{PROJECT_ROOT}/dev.db")

from a2wsgi import ASGIMiddleware
from app.main import app as asgi_app

application = ASGIMiddleware(asgi_app)
