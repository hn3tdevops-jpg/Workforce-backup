#!/usr/bin/env bash
set -euo pipefail

cd ~/projects_active

echo "==> Ensuring target directories exist"
mkdir -p apps/api/app/api/v1/endpoints
mkdir -p apps/api/app/api
mkdir -p apps/api/app/core
mkdir -p apps/api/app/db
mkdir -p apps/api/app/models
mkdir -p apps/api/app/schemas
mkdir -p apps/api/app/services
mkdir -p apps/api/app/integrations
mkdir -p tests

echo "==> Ensuring package markers exist"
touch apps/__init__.py
touch apps/api/__init__.py
touch apps/api/app/__init__.py
touch apps/api/app/api/__init__.py
touch apps/api/app/api/v1/__init__.py
touch apps/api/app/api/v1/endpoints/__init__.py
touch apps/api/app/core/__init__.py
touch apps/api/app/db/__init__.py
touch apps/api/app/models/__init__.py
touch apps/api/app/schemas/__init__.py
touch apps/api/app/services/__init__.py
touch apps/api/app/integrations/__init__.py

echo "==> Writing FastAPI root app if missing"
if [ ! -f apps/api/app/main.py ]; then
cat > apps/api/app/main.py <<'EOF'
from fastapi import FastAPI

from apps.api.app.api.router import api_router

app = FastAPI(title="Workforce API", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Workforce API is running"}
EOF
fi

echo "==> Writing API router"
cat > apps/api/app/api/router.py <<'EOF'
from fastapi import APIRouter

from apps.api.app.api.v1.endpoints import assignments, health, rooms, shifts, tasks

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(assignments.router, prefix="/assignments", tags=["assignments"])
api_router.include_router(shifts.router, prefix="/shifts", tags=["shifts"])
EOF

echo "==> Writing endpoints"
cat > apps/api/app/api/v1/endpoints/health.py <<'EOF'
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
EOF

cat > apps/api/app/api/v1/endpoints/rooms.py <<'EOF'
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_rooms() -> dict[str, list]:
    return {"items": []}
EOF

cat > apps/api/app/api/v1/endpoints/tasks.py <<'EOF'
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_tasks() -> dict[str, list]:
    return {"items": []}
EOF

cat > apps/api/app/api/v1/endpoints/assignments.py <<'EOF'
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_assignments() -> dict[str, list]:
    return {"items": []}
EOF

cat > apps/api/app/api/v1/endpoints/shifts.py <<'EOF'
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_shifts() -> dict[str, list]:
    return {"items": []}
EOF

echo "==> Writing starter services"
cat > apps/api/app/services/housekeeping_service.py <<'EOF'
class HousekeepingService:
    def summarize(self) -> dict[str, str]:
        return {"status": "ready"}


housekeeping_service = HousekeepingService()
EOF

cat > apps/api/app/services/room_board_service.py <<'EOF'
class RoomBoardService:
    def build_board(self) -> dict[str, list]:
        return {"rooms": []}


room_board_service = RoomBoardService()
EOF

echo "==> Writing starter schemas"
cat > apps/api/app/schemas/room.py <<'EOF'
from pydantic import BaseModel


class RoomRead(BaseModel):
    id: int
    room_number: str
    status: str
EOF

cat > apps/api/app/schemas/task.py <<'EOF'
from pydantic import BaseModel


class TaskRead(BaseModel):
    id: int
    title: str
    status: str
EOF

cat > apps/api/app/schemas/assignment.py <<'EOF'
from pydantic import BaseModel


class AssignmentRead(BaseModel):
    id: int
    task_id: int
    assigned_to_user_id: int
    status: str
EOF

cat > apps/api/app/schemas/shift.py <<'EOF'
from pydantic import BaseModel


class ShiftRead(BaseModel):
    id: int
    title: str
    status: str
EOF

echo "==> Writing starter tests"
cat > tests/test_api_phase3.py <<'EOF'
from fastapi.testclient import TestClient

from apps.api.app.main import app

client = TestClient(app)


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_health() -> None:
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rooms() -> None:
    response = client.get("/api/v1/rooms/")
    assert response.status_code == 200


def test_tasks() -> None:
    response = client.get("/api/v1/tasks/")
    assert response.status_code == 200


def test_assignments() -> None:
    response = client.get("/api/v1/assignments/")
    assert response.status_code == 200


def test_shifts() -> None:
    response = client.get("/api/v1/shifts/")
    assert response.status_code == 200
EOF

echo "==> Patching pyproject.toml if needed"
if [ -f pyproject.toml ]; then
  grep -q 'where = \["apps", "packages"\]' pyproject.toml || cat >> pyproject.toml <<'EOF'

[tool.setuptools.packages.find]
where = ["apps", "packages"]
EOF
fi

echo "==> Writing architecture note"
mkdir -p docs/architecture
cat > docs/architecture/PHASE3_BOOTSTRAP.md <<'EOF'
# Phase 3 Bootstrap

This bootstrap added:
- canonical FastAPI entrypoint at apps/api/app/main.py
- API router wiring
- starter endpoints for health, rooms, tasks, assignments, shifts
- starter services and schemas
- API smoke tests

Next:
- wire real models
- connect database session
- add CRUD
- enforce RBAC
- attach housekeeping workflow rules
EOF

echo "==> Running compile validation"
python -m compileall apps packages tests || true

echo
echo "Phase 3 bootstrap complete."
echo
echo "Run next:"
echo "  pytest"
echo "  ruff check ."
echo "  uvicorn apps.api.app.main:app --reload"