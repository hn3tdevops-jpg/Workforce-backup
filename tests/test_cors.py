import importlib
import os
import sys

# Ensure CORS env is set before importing the FastAPI app
os.environ.setdefault("CORS_ALLOW_ORIGINS", "https://example.com")

# If module already imported in this process, reload to pick up env change
if "apps.api.app.main" in sys.modules:
    importlib.reload(sys.modules["apps.api.app.main"])

from fastapi.testclient import TestClient

from apps.api.app.main import app

client = TestClient(app)


def test_cors_allows_allowed_origin():
    resp = client.options(
        "/",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.status_code == 200
    assert (
        resp.headers.get("access-control-allow-origin")
        == "https://example.com"
    )


def test_cors_denies_disallowed_origin():
    resp = client.options(
        "/",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Preflight still returns 200 but should not include allow-origin for disallowed hosts
    assert resp.status_code in (200, 400)
    assert resp.headers.get("access-control-allow-origin") is None
