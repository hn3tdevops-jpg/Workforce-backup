# Workforce
Workforce Suite

## Phase 1 — Multi-tenant Scaffold

### Prerequisites
- Python 3.12+
- [Poetry](https://python-poetry.org/) (`pip install poetry`)
- PostgreSQL (for production) or SQLite (for local dev/testing)

### Setup

```bash
# 1. Install dependencies
poetry install

# 2. Configure environment (copy and edit)
cp .env.example .env
# Set DATABASE_URL, SECRET_KEY, APP_ENV in .env

# 3. Run database migrations
poetry run alembic upgrade head

# 4. Start the development server
poetry run uvicorn app.main:app --reload

Development (alternative):
Run the provided development script for live reload and a consistent entrypoint:

    ./scripts/run_uvicorn.sh

Or run directly (explicit path to app):

    uvicorn apps.api.app.main:app --reload --host 0.0.0.0 --port 8000


```

The API will be available at `http://localhost:8000/api/v1`.

### Bootstrap endpoint

On first run (when no users exist), call the bootstrap endpoint to create the
initial Business, Location, and admin User:

```bash
curl -X POST http://localhost:8000/api/v1/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "admin_email": "admin@hn3t.org",
    "admin_password": "@DM!N12345",
    "business_name":  HN3T",
    "location_name": "HQ"
  }'
```

Returns `201` with `business_id`, `location_id`, and `user_id`.

### Running tests

```bash
poetry run pytest tests/ -v
```

### Environment variables

| Variable       | Description                          | Default                        |
|----------------|--------------------------------------|--------------------------------|
| `DATABASE_URL` | Async SQLAlchemy DB URL              | `sqlite+aiosqlite:///./workforce.db` |
| `APP_ENV`      | Application environment              | `development`                  |
| `SECRET_KEY`   | Secret key for token signing         | `changeme` (**change this!**)  |

## HN3T Master Plan

The canonical project roadmap lives in [HN3T_MASTER_PLAN.md](./HN3T_MASTER_PLAN.md). Note: HN3T_MASTER_PLAN.md is the canonical roadmap; MASTER_PLAN.md is kept only for backward-compatibility.

## Developer test setup (venv)

If running tests without Poetry, use a virtualenv and install the package in editable mode plus test deps:

```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e . --no-deps   # install this package in editable mode
pip install pytest pytest-asyncio anyio pydantic-settings 'pydantic[email]' bcrypt==3.2.0 aiosqlite alembic fastapi uvicorn sqlalchemy python-jose passlib httpx asyncpg
# Note: asgi2wsgi>=0.4.0 may be required by some workflows; if needed, install it separately:
# pip install asgi2wsgi
pytest -q
```

Notes:
- pydantic-settings and email-validator may be required for tests.
- bcrypt is pinned to 3.2.0 for compatibility.
- If pip reports missing extra packages, install them as shown above.
