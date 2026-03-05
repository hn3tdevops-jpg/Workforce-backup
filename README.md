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
```

The API will be available at `http://localhost:8000/api/v1`.

### Bootstrap endpoint

On first run (when no users exist), call the bootstrap endpoint to create the
initial Business, Location, and admin User:

```bash
curl -X POST http://localhost:8000/api/v1/bootstrap \
  -H "Content-Type: application/json" \
  -d '{
    "admin_email": "admin@example.com",
    "admin_password": "YourSecurePassword",
    "business_name": "My Business",
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
