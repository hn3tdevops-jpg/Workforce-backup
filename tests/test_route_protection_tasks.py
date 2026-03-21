import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.access_control import Membership, Role, ScopedRoleAssignment
from app.models.tenant import Business, Location, Tenant
from app.models.user import User
from app.services.rbac_seed_service import async_seed_default_roles_for_business


async def seed_user(
    db_session: AsyncSession,
    *,
    with_membership: bool,
    with_owner_assignment: bool,
) -> tuple[str, uuid.UUID]:
    tenant = Tenant(id=uuid.uuid4(), name="Tenant 1", slug=f"tenant-{uuid.uuid4().hex[:8]}")
    business = Business(id=uuid.uuid4(), tenant_id=tenant.id, name="Business 1")
    location = Location(id=uuid.uuid4(), business_id=business.id, name="Location A")
    user = User(
        id=uuid.uuid4(),
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="not-real",
        business_id=business.id,
        is_active=True,
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

    token = create_access_token(
        user_id=str(user.id),
        business_id=str(business.id),
    )
    return token, business.id


@pytest.mark.asyncio
async def test_tasks_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/api/v1/tasks/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required."


@pytest.mark.asyncio
async def test_tasks_allows_user_with_hk_tasks_manage(client: AsyncClient, db_session: AsyncSession) -> None:
    token, _business_id = await seed_user(
        db_session,
        with_membership=True,
        with_owner_assignment=True,
    )

    response = await client.get(
        "/api/v1/tasks/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_tasks_forbids_user_without_permission(client: AsyncClient, db_session: AsyncSession) -> None:
    token, _business_id = await seed_user(
        db_session,
        with_membership=False,
        with_owner_assignment=False,
    )

    response = await client.get(
        "/api/v1/tasks/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not enough permissions."