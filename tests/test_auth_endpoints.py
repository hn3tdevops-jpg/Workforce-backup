import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.access_control import Membership, Role, ScopedRoleAssignment
from app.models.tenant import Business, Location, Tenant
from app.models.user import User
from app.services.rbac_seed_service import async_seed_default_roles_for_business


async def seed_user(
    db_session: AsyncSession,
    *,
    password: str = "LoginPass1!",
    is_active: bool = True,
    with_membership: bool = True,
    with_owner_assignment: bool = True,
) -> tuple[User, Business]:
    tenant = Tenant(id=uuid.uuid4(), name="Tenant 1", slug=f"tenant-{uuid.uuid4().hex[:8]}")
    business = Business(id=uuid.uuid4(), tenant_id=tenant.id, name="Business 1")
    location = Location(id=uuid.uuid4(), business_id=business.id, name="Location A")
    user = User(
        id=uuid.uuid4(),
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password=hash_password(password),
        business_id=business.id,
        is_active=is_active,
    )

    db_session.add_all([tenant, business, location, user])
    await db_session.flush()

    if with_membership:
        membership = Membership(
            id=uuid.uuid4(),
            user_id=user.id,
            business_id=business.id,
            status="active",
            is_owner=with_owner_assignment,
        )
        db_session.add(membership)
        await db_session.flush()

        if with_owner_assignment:
            await async_seed_default_roles_for_business(db_session, business.id)
            owner_role = await db_session.scalar(
                select(Role).where(
                    Role.business_id == business.id,
                    Role.name == "Owner",
                )
            )
            db_session.add(
                ScopedRoleAssignment(
                    id=uuid.uuid4(),
                    membership_id=membership.id,
                    role_id=owner_role.id,
                    location_id=None,
                )
            )

    await db_session.commit()
    return user, business


@pytest.mark.asyncio
async def test_login_succeeds_with_valid_credentials(client: AsyncClient, db_session: AsyncSession) -> None:
    user, business = await seed_user(db_session)

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "LoginPass1!",
        },
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["business_id"] == str(business.id)
    assert data["user"]["email"] == user.email


@pytest.mark.asyncio
async def test_login_fails_with_wrong_password(client: AsyncClient, db_session: AsyncSession) -> None:
    user, _business = await seed_user(db_session)

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "WrongPass1!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.asyncio
async def test_login_fails_for_inactive_user(client: AsyncClient, db_session: AsyncSession) -> None:
    user, _business = await seed_user(db_session, is_active=False)

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "LoginPass1!",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Inactive user."


@pytest.mark.asyncio
async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


@pytest.mark.asyncio
async def test_me_returns_user_roles_and_permissions(client: AsyncClient, db_session: AsyncSession) -> None:
    user, business = await seed_user(db_session)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "LoginPass1!",
        },
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    data = response.json()

    assert data["user"]["id"] == str(user.id)
    assert data["user"]["email"] == user.email
    assert data["business_id"] == str(business.id)
    assert "Owner" in data["roles"]
    assert "hk.rooms.read" in data["permissions"]
    assert "hk.tasks.manage" in data["permissions"]
    assert "schedule.read" in data["permissions"]
    assert "time.read" in data["permissions"]
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["business_id"] == str(business.id)