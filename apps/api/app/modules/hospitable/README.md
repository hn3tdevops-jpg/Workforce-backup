# Hospitable Module — Silver Sands Integration

This module adds full property operations (housekeeping, maintenance, inventory) to the Workforce platform.

## Architecture

```
apps/api/app/modules/hospitable/
├── models/property_ops.py       # SQLAlchemy ORM models
├── schemas/room_ops.py          # Pydantic request/response schemas
├── services/room_ops_service.py # Business logic layer
├── api/router.py                # FastAPI router (mounted at /api/v1/hospitable)
└── seeds/silver_sands_seed.py   # Silver Sands Motel seed data
```

## Setup

### 1. Run migrations

```bash
# From repo root
PYTHONPATH=apps/api python3 -m alembic upgrade head
```

### 2. Seed Silver Sands layout

```bash
PYTHONPATH=apps/api python3 -m apps.api.app.modules.hospitable.seeds.silver_sands_seed
```

Note the `location_id` from the output — you'll need it for the frontend.

### 3. Configure frontend

```bash
# apps/web/hospitable-web/.env.local
NEXT_PUBLIC_LOCATION_ID=<uuid-from-seed-output>
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/hospitable/rooms` | List rooms with filters |
| POST | `/api/v1/hospitable/rooms` | Create a room |
| PATCH | `/api/v1/hospitable/rooms/{id}/status` | Update room status |
| POST | `/api/v1/hospitable/rooms/bulk-status` | Bulk update room statuses |
| GET | `/api/v1/hospitable/tasks` | List housekeeping tasks |
| POST | `/api/v1/hospitable/tasks` | Create a task |
| PATCH | `/api/v1/hospitable/tasks/{id}/status` | Update task status |
| GET | `/api/v1/hospitable/maintenance/issues` | List maintenance issues |
| POST | `/api/v1/hospitable/maintenance/issues` | Report an issue |
| PATCH | `/api/v1/hospitable/maintenance/issues/{id}` | Update an issue |
| GET | `/api/v1/hospitable/dashboard/summary` | Operational dashboard summary |
| GET | `/api/v1/hospitable/dashboard/housekeeping-board` | Active HK tasks |
| GET | `/api/v1/hospitable/dashboard/maintenance-board` | Open maintenance issues |
| GET | `/api/v1/hospitable/locations/{id}/property-tree` | Property hierarchy |

## Silver Sands Layout

- **Building 1** → **Floor 1**
  - **North Side** (rooms 7–12): 2-queen beds, North Group
  - **South Side** (rooms 1–6): 1-king beds, South Group
- 12 rooms total, each with 5 assets and 10 supply par entries
