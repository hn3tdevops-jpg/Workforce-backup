import pytest

from tests.test_auth_endpoints import seed_user


@pytest.mark.asyncio
async def test_get_my_businesses_requires_auth(client):
    res = await client.get("/api/v1/me/businesses")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_get_my_businesses_returns_list(client, db_session):
    user, business = await seed_user(db_session)

    # Login to obtain token
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "LoginPass1!"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/me/businesses", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert any(item["id"] == str(business.id) for item in data)

    # The business in the token should be marked as default
    found = next((item for item in data if item["id"] == str(business.id)), None)
    assert found is not None
    assert found.get("is_default") is True
