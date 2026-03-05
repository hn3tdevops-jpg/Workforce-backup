import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_bootstrap_creates_entities(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/bootstrap",
        json={
            "admin_email": "hn3torg@gmail.com",
            "admin_password": "Punk@$$3773",
            "business_name": "HN3T Org",
            "location_name": "HQ",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert "business_id" in data
    assert "location_id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_bootstrap_forbidden_when_users_exist(client: AsyncClient) -> None:
    # Second call should be forbidden
    response = await client.post(
        "/api/v1/bootstrap",
        json={
            "admin_email": "second@example.com",
            "admin_password": "AnotherPass1!",
            "business_name": "Another Org",
            "location_name": "Branch",
        },
    )
    assert response.status_code == 403
