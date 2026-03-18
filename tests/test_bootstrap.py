import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_bootstrap_creates_entities(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/bootstrap",
        json={
            "admin_email": "hn3torg@gmail.com",
            "admin_password": "BootstrapPass1!",
            "business_name": "HN3T Org",
            "location_name": "HQ",
        },
    )

    assert response.status_code == 201, response.text

    data = response.json()
    assert data["business_id"]
    assert data["location_id"]
    assert data["user_id"]


@pytest.mark.asyncio
async def test_bootstrap_forbidden_when_users_exist(client: AsyncClient) -> None:
    first = await client.post(
        "/api/v1/bootstrap",
        json={
            "admin_email": "first@example.com",
            "admin_password": "BootstrapPass1!",
            "business_name": "First Org",
            "location_name": "HQ",
        },
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        "/api/v1/bootstrap",
        json={
            "admin_email": "second@example.com",
            "admin_password": "AnotherPass1!",
            "business_name": "Another Org",
            "location_name": "Branch",
        },
    )
    assert second.status_code == 403
    assert second.json()["detail"] == "Bootstrap is only allowed when no users exist."
