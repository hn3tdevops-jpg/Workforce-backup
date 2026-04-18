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


async def add_second_business_membership(
    db_session: AsyncSession,
    user: User,
    base_business: Business,
) -> Business:
    second_business = Business(
        id=uuid.uuid4(),
        tenant_id=base_business.tenant_id,
        name="Business 2",
    )
    second_location = Location(
        id=uuid.uuid4(),
        business_id=second_business.id,
        name="Location B",
    )
    second_membership = Membership(
        id=uuid.uuid4(),
        user_id=user.id,
        business_id=second_business.id,
        status="active",
        is_owner=True,
    )

    db_session.add_all([second_business, second_location, second_membership])
    await db_session.flush()

    await async_seed_default_roles_for_business(db_session, second_business.id)
    owner_role = await db_session.scalar(
        select(Role).where(
            Role.business_id == second_business.id,
            Role.name == "Owner",
        )
    )
    db_session.add(
        ScopedRoleAssignment(
            id=uuid.uuid4(),
            membership_id=second_membership.id,
            role_id=owner_role.id,
            location_id=None,
        )
    )

    await db_session.commit()
    return second_business


async def create_unrelated_business(db_session: AsyncSession) -> Business:
    tenant = Tenant(id=uuid.uuid4(), name="Other Tenant", slug=f"tenant-{uuid.uuid4().hex[:8]}")
    business = Business(id=uuid.uuid4(), tenant_id=tenant.id, name="Other Business")
    location = Location(id=uuid.uuid4(), business_id=business.id, name="Other Location")
    db_session.add_all([tenant, business, location])
    await db_session.commit()
    return business


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


@pytest.mark.asyncio
async def test_switch_business_requires_authentication(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/switch-business",
        json={"business_id": str(uuid.uuid4())},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


@pytest.mark.asyncio
async def test_switch_business_succeeds_for_active_membership(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user, business1 = await seed_user(db_session)
    business2 = await add_second_business_membership(db_session, user, business1)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "LoginPass1!",
        },
    )
    assert login_response.status_code == 200, login_response.text
    token1 = login_response.json()["access_token"]
    assert login_response.json()["business_id"] == str(business1.id)

    switch_response = await client.post(
        "/api/v1/auth/switch-business",
        json={"business_id": str(business2.id)},
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert switch_response.status_code == 200, switch_response.text

    switched = switch_response.json()
    assert switched["access_token"]
    assert switched["token_type"] == "bearer"
    assert switched["business_id"] == str(business2.id)
    assert "Owner" in switched["roles"]
    assert "schedule.read" in switched["permissions"]

    token2 = switched["access_token"]
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert me_response.status_code == 200, me_response.text
    me_data = me_response.json()
    assert me_data["business_id"] == str(business2.id)
    assert len(me_data["memberships"]) == 2
    assert "Owner" in me_data["roles"]


@pytest.mark.asyncio
async def test_switch_business_forbidden_without_membership(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user, business1 = await seed_user(db_session)
    unrelated_business = await create_unrelated_business(db_session)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": user.email,
            "password": "LoginPass1!",
        },
    )
    assert login_response.status_code == 200, login_response.text
    token = login_response.json()["access_token"]
    assert login_response.json()["business_id"] == str(business1.id)

    switch_response = await client.post(
        "/api/v1/auth/switch-business",
        json={"business_id": str(unrelated_business.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert switch_response.status_code == 403
    assert switch_response.json()["detail"] == "User does not have access to that business."


# --- New tests for /auth/register ---
@pytest.mark.asyncio
async def test_register_creates_user(client: AsyncClient, db_session: AsyncSession) -> None:
    email = f"reg-{uuid.uuid4().hex[:8]}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "RegPass1!"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == email

    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None


@pytest.mark.asyncio
async def test_register_duplicate_fails(client: AsyncClient) -> None:
    email = f"dup-{uuid.uuid4().hex[:8]}@example.com"
    resp1 = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "RegPass1!"},
    )
    assert resp1.status_code == 201, resp1.text

    resp2 = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "OtherPass1!"},
    )
    assert resp2.status_code == 400
    assert "Email already registered" in resp2.json().get("detail", "")
