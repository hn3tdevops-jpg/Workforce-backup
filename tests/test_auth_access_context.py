"""Tests for GET /api/v1/auth/me/access-context."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_auth_endpoints import seed_user


@pytest.mark.asyncio
async def test_access_context_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me/access-context")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


@pytest.mark.asyncio
async def test_access_context_returns_roles_and_permissions(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user, business = await seed_user(db_session)

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "LoginPass1!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me/access-context",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["assignment"]["user_id"] == str(user.id)
    assert data["assignment"]["business_id"] == str(business.id)
    assert isinstance(data["scope"]["roles"], list)
    assert isinstance(data["scope"]["permissions"], list)
    assert "Owner" in data["scope"]["roles"]
    assert len(data["scope"]["permissions"]) > 0


@pytest.mark.asyncio
async def test_access_context_compat_scope_format(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user, business = await seed_user(db_session)

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "LoginPass1!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me/access-context",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    compat = response.json()["compat"]

    assert compat.startswith("COMPAT:")
    assert f"user={user.id}" in compat
    assert f"business={business.id}" in compat


@pytest.mark.asyncio
async def test_access_context_no_membership_forbidden(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Seed a user with no membership so that after forced-token issuance the
    # endpoint rejects the request.
    user, business = await seed_user(
        db_session,
        with_membership=False,
        with_owner_assignment=False,
    )

    # Manually forge a token with a business_id that the user has no membership for
    from apps.api.app.core.security import create_access_token

    token = create_access_token(
        user_id=str(user.id),
        business_id=str(business.id),
    )

    response = await client.get(
        "/api/v1/auth/me/access-context",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert "active membership" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_access_context_does_not_expose_employee_data(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """The response must not contain any employee-specific fields."""
    user, business = await seed_user(db_session)

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "LoginPass1!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me/access-context",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()

    # Employee-specific keys must not appear in the response
    for forbidden_key in ("employee_id", "employee", "pin", "hire_date"):
        assert forbidden_key not in data
        assert forbidden_key not in data.get("assignment", {})
        assert forbidden_key not in data.get("scope", {})
