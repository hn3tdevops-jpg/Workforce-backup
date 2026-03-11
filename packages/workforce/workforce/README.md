# Workforce Management MVP

Multi-tenant workforce scheduling system built with **FastAPI + SQLAlchemy 2 + Alembic**.

---

## Quick-start (local / PythonAnywhere console)

```bash
# 1. Create and activate a virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -U pip

# 2. Install the project
cd workforce
pip install -e .

# 3. Copy and edit environment variables
cp .env.example .env
# Edit .env if you want Postgres: DATABASE_URL=postgresql+psycopg://user:pass@host/dbname

# 4. Run migrations
alembic upgrade head

# 5. Seed demo dataset
python -m app.cli.main seed-demo

# 6. Start the development server (console / SSH)
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Environment variables

| Variable                       | Default                  | Description                                      |
|--------------------------------|--------------------------|--------------------------------------------------|
| `DATABASE_URL`                 | `sqlite:///./dev.db`     | SQLAlchemy URL; use absolute path on PA          |
| `ENV`                          | `dev`                    | `dev` / `prod`                                   |
| `LOG_LEVEL`                    | `INFO`                   | Python logging level                             |
| `SECRET_KEY`                   | *(placeholder)*          | **Change in production** — 256-bit random string |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | `60`                     | JWT access token lifetime                        |
| `REFRESH_TOKEN_EXPIRE_DAYS`    | `7`                      | Refresh token lifetime                           |
| `ENABLE_BOOTSTRAP`             | `false`                  | Enable the one-time superadmin bootstrap endpoint |
| `BOOTSTRAP_TOKEN`              | *(unset)*                | Secret token required by the bootstrap endpoint  |

Set these in `.env` (local) or via the **PythonAnywhere → Files → .env** or via the
Web tab environment variable editor.

---

## CLI commands

```bash
# Migrate database (alias for alembic upgrade head)
python -m app.cli.main init-db

# Create demo data
python -m app.cli.main seed-demo

# Create HKops demo rooms and tasks
python -m app.cli.main seed-hk-demo

# Find candidates for a shift (prints ranked list)
python -m app.cli.main match --shift-id <UUID>

# Purge expired messages + stale refresh tokens (run periodically in prod)
python -m app.cli.main purge
```

---

## API endpoints

### Legacy (v0)

| Method | Path | Description |
|--------|------|-------------|
| GET    | `/health` | Health check |
| POST   | `/businesses` | Create a business |
| POST   | `/businesses/{id}/locations` | Add a location |
| POST   | `/employees` | Create an employee |
| POST   | `/businesses/{id}/employments` | Hire employee into a business |
| POST   | `/employments/{id}/roles` | Assign a role to an employment |
| POST   | `/availability` | Create an availability block |
| POST   | `/shifts` | Create a shift |
| GET    | `/shifts/{id}/candidates` | Get ranked candidates for a shift |
| POST   | `/training/modules` | Create a training module |
| POST   | `/training/records` | Record employee training |

### V1 Auth

| Method | Path | Description |
|--------|------|-------------|
| POST   | `/api/v1/auth/login` | Login → access + refresh tokens |
| POST   | `/api/v1/auth/refresh` | Refresh access token |
| POST   | `/api/v1/auth/logout` | Revoke refresh token |
| POST   | `/api/v1/auth/register` | Self-register |
| POST   | `/api/v1/auth/bootstrap` | One-time superadmin bootstrap (requires feature flag + token) |

#### Bootstrap endpoint

The bootstrap endpoint creates the **initial superadmin account** when the database
contains no users.  It is disabled by default and protected by a one-time token.

```bash
# 1. Generate a strong random token
export BOOTSTRAP_TOKEN="$(openssl rand -hex 24)"

# 2. Enable the endpoint (set in .env or shell before starting the server)
export ENABLE_BOOTSTRAP=true

# 3. Start the server, then POST to the endpoint
curl -X POST http://localhost:8000/api/v1/auth/bootstrap \
     -H "Content-Type: application/json" \
     -H "X-Bootstrap-Token: $BOOTSTRAP_TOKEN" \
     -d '{"email":"admin@example.com","password":"ChangeMeNow!","first_name":"Super","last_name":"Admin"}'

# 4. After the superadmin is created, disable the endpoint
export ENABLE_BOOTSTRAP=false
# (or remove it from .env and restart the server)
```

> **Security note:** `ENABLE_BOOTSTRAP` defaults to `false`.  Set it to `true` only
> during initial provisioning, then turn it off immediately.  Never expose
> `BOOTSTRAP_TOKEN` in source control or logs.

### V1 Timeclock (worker)

| Method | Path | Description |
|--------|------|-------------|
| POST   | `/api/v1/worker/me/timeclock/{biz}/clock-in` | Clock in |
| POST   | `/api/v1/worker/me/timeclock/{biz}/clock-out` | Clock out |
| GET    | `/api/v1/worker/me/timeclock/{biz}/status` | Current clock status |
| GET    | `/api/v1/worker/me/timeclock/{biz}/entries` | My time entries |

### V1 Timeclock (tenant/admin)

| Method | Path | Description |
|--------|------|-------------|
| GET    | `/api/v1/tenant/{biz}/timeclock/live` | Live clock-in view |
| GET    | `/api/v1/tenant/{biz}/timeclock/timecards` | Date-range timecard rollup |
| GET    | `/api/v1/tenant/{biz}/timeclock/summary` | Hours per user (all time) |
| PATCH  | `/api/v1/tenant/{biz}/timeclock/{entry_id}` | Admin correction (requires `timeclock:manage`) |
| GET    | `/api/v1/tenant/{biz}/timeclock/status/{user_id}` | Service-to-service: clock status for any user |

### V1 Marketplace / Swap flow

| Method | Path | Description |
|--------|------|-------------|
| GET    | `/api/v1/marketplace/postings` | Public job board |
| POST   | `/api/v1/worker/me/marketplace/{biz}/swap-requests` | Create swap request |
| POST   | `/api/v1/worker/me/marketplace/{biz}/swap-requests/{id}/initiator-approve` | Initiator approves |
| POST   | `/api/v1/worker/me/marketplace/{biz}/swap-requests/{id}/respond` | Peer accepts/denies (`?accept=true/false`) |
| POST   | `/api/v1/tenant/{biz}/marketplace/swap-requests/{id}/arrange-coverage` | Manager arranges coverage |

Swap states: `pending` → `awaiting_peer` → `approved` / `denied` / `pending_coverage` → `completed`  
SwapPermissionRule: highest `priority` wins; `allow` = auto-approve, `deny` = block.

### V1 Integration (service-to-service, used by Housekeeping)

| Method | Path | Permission required | Description |
|--------|------|---------------------|-------------|
| GET    | `/api/v1/tenant/{biz}/integrations/staff` | `members:read` | List active staff (filter by location/role) |
| GET    | `/api/v1/tenant/{biz}/timeclock/status/{user_id}` | `timeclock:manage` | Clock status for a user |
| POST   | `/api/v1/tenant/{biz}/integrations/hk-events` | `members:read` | Receive housekeeping task events (task_assigned, task_completed) |

Interactive docs: `http://localhost:8000/docs`

---

## Run tests

```bash
pytest -q
```

---

## PythonAnywhere Web App deployment

### Step 1 — Open a Bash console and set up the project

```bash
cd ~
git clone https://github.com/hn3tdevops-jpg/scheduler.git
cd scheduler/workforce
python3.11 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -e .
cp .env.example .env
alembic upgrade head
python -m app.cli.main seed-demo
```

### Step 2 — Set environment variables

Edit `~/scheduler/workforce/.env`:

```
DATABASE_URL=sqlite:////home/<your-username>/scheduler/workforce/dev.db
ENV=prod
LOG_LEVEL=INFO
```

Replace `<your-username>` with your PythonAnywhere username.

### Step 3 — Configure the Web tab

1. Go to **Web** tab → **Add a new web app** → **Manual configuration** → **Python 3.11**.
2. Set the **Virtualenv** path to `/home/<your-username>/scheduler/workforce/venv`.

### Step 4 — WSGI configuration file

PythonAnywhere's free/hacker tier uses **WSGI (not ASGI)**. FastAPI is an ASGI app, so
we use `a2wsgi` as a thin adapter.

**Install the adapter:**

```bash
source ~/scheduler/workforce/venv/bin/activate
pip install a2wsgi
```

**Edit the WSGI file** (PythonAnywhere auto-creates it at
`/var/www/<username>_pythonanywhere_com_wsgi.py`).  
Replace the entire file content with:

```python
import sys
import os

# Add project to path
project_home = '/home/<your-username>/scheduler/workforce'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Wrap FastAPI (ASGI) in a WSGI adapter
from a2wsgi import ASGIMiddleware
from app.main import app as fastapi_app

application = ASGIMiddleware(fastapi_app)
```

> **Note:** Replace `<your-username>` with your actual PythonAnywhere username.

### Step 5 — Reload and verify

1. Click **Reload** on the Web tab.
2. Open `https://<your-username>.pythonanywhere.com/health`

Expected response:
```json
{"status": "ok", "env": "prod", "time": "..."}
```

### Step 6 — Test candidates endpoint after seed

```bash
# In PythonAnywhere console — get the shift ID from seed output
SHIFT_ID=<uuid-from-seed-demo-output>

curl https://<your-username>.pythonanywhere.com/shifts/${SHIFT_ID}/candidates
```

---

## Verification commands (summary)

```bash
# Migrate
alembic upgrade head

# Seed
python -m app.cli.main seed-demo
# Note the Shift ID printed — use it below

# Tests
pytest -q

# Health check
curl http://localhost:8000/health

# Candidates (replace UUID with output from seed-demo)
curl http://localhost:8000/shifts/<shift-id>/candidates
```

---

## Architecture notes

- **Tenant safety**: every candidate query joins through `Employment` filtered on `business_id` — cross-tenant leakage is impossible.
- **Audit log**: every POST (API and CLI seed) writes an `AuditLog` row with `before_json` / `after_json`.
- **Matching rules**: candidates must have active employment in the shift's business, hold the correct role, have non-`unavailable` availability covering the full shift window, and must not have an overlapping `offered/assigned/checked_in` assignment on any other shift.
- **Postgres/SQLite parity**: same ORM models; `render_as_batch=True` in Alembic env handles SQLite DDL limitations.
