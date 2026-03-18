from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_health() -> None:
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rooms_requires_authentication() -> None:
    response = client.get("/api/v1/rooms/")
    assert response.status_code == 401

def test_tasks_requires_authentication() -> None:
    response = client.get("/api/v1/tasks/")
    assert response.status_code == 401

def test_assignments_requires_authentication() -> None:
    response = client.get("/api/v1/assignments/")
    assert response.status_code == 401


def test_shifts_requires_authentication() -> None:
    response = client.get("/api/v1/shifts/")
    assert response.status_code == 401
