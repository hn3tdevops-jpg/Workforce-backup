import pytest

from tests.test_auth_endpoints import seed_user


@pytest.mark.asyncio
async def test_get_my_effective_permissions_returns_list(client, db_session):
    user, business = await seed_user(db_session)

    res = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "LoginPass1!"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get(
        f"/api/v1/me/effective-permissions?business_id={business.id}",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
