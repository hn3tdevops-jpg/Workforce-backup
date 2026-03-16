import os
import sys

project_home = os.path.abspath(os.path.dirname(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from dotenv import load_dotenv

env_path = os.environ.get("WORKFORCE_ENV_FILE", os.path.join(project_home, ".env"))
load_dotenv(env_path)

os.environ.setdefault("ENV", "prod")
os.environ.setdefault("DATABASE_URL", f"sqlite:////{project_home}/dev.db")

from a2wsgi import ASGIMiddleware
from apps.api.app.main import app as asgi_app

application = ASGIMiddleware(asgi_app)
