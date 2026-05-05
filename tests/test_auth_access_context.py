"""Tests for GET /api/v1/auth/me/access-context (COMPAT scope)."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.security import create_access_token
from tests.test_auth_endpoints import seed_user


@pytest.mark.asyncio
async def test_access_context_unauthenticated_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me/access-context")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


@pytest.mark.asyncio
async def test_access_context_authenticated_member_returns_200(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user, business = await seed_user(db_session)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "LoginPass1!"},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me/access-context",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["user_id"] == str(user.id)
    assert data["has_access"] is True
    assert "resolved_at" in data


@pytest.mark.asyncio
async def test_access_context_includes_effective_permissions(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user, business = await seed_user(db_session)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "LoginPass1!"},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me/access-context",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data["scopes"]) == 1
    scope = data["scopes"][0]
    assert isinstance(scope["effective_permissions"], list)
    assert len(scope["effective_permissions"]) > 0
    # Owner role should carry standard permissions
    assert "hk.rooms.read" in scope["effective_permissions"]
    assert scope["link_status"] == "COMPAT"
    assert scope["employment_status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_access_context_compat_scope_count_is_one(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user, business = await seed_user(db_session)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "LoginPass1!"},
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me/access-context",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["active_scope_count"] == 1
    assert len(data["scopes"]) == 1


@pytest.mark.asyncio
async def test_access_context_no_membership_returns_no_scope(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    # Create a user without a membership; forge a valid token with the
    # business_id to simulate a stale or manually-crafted token.
    user, business = await seed_user(db_session, with_membership=False)
    token = create_access_token(
        user_id=str(user.id),
        business_id=str(business.id),
    )

    response = await client.get(
        "/api/v1/auth/me/access-context",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["has_access"] is False
    assert data["active_scope_count"] == 0
    assert data["scopes"] == []
