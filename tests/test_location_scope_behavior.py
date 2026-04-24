import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.access_control import Membership, Role, ScopedRoleAssignment
from app.models.tenant import Business, Location, Tenant
from app.models.user import User
from app.services.rbac_seed_service import \
    async_seed_default_roles_for_business


async def setup_user(db_session: AsyncSession):
    tenant = Tenant(
        id=uuid.uuid4(), name="Tenant X", slug=f"tenant-{uuid.uuid4().hex[:8]}"
    )
    business = Business(
        id=uuid.uuid4(), tenant_id=tenant.id, name="Business X"
    )
    location = Location(
        id=uuid.uuid4(), business_id=business.id, name="Location X"
    )
    user = User(
        id=uuid.uuid4(),
        email=f"user-{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="not-real",
        business_id=business.id,
        is_active=True,
    )

    db_session.add_all([tenant, business, location, user])
    await db_session.flush()

    membership = Membership(
        id=uuid.uuid4(),
        user_id=user.id,
        business_id=business.id,
        status="active",
        is_owner=False,
    )
    db_session.add(membership)
    await db_session.flush()

    # Seed default roles and permissions for the business
    await async_seed_default_roles_for_business(db_session, business.id)

    await db_session.commit()

    token = create_access_token(
        user_id=str(user.id), business_id=str(business.id)
    )
    return token, business, location, membership


@pytest.mark.asyncio
async def test_allows_user_with_location_scoped_role(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token, business, location, membership = await setup_user(db_session)

    # Find the Owner role (created by seeding) to attach at a location
    owner_role = await db_session.scalar(
        select(Role).where(
            Role.business_id == business.id, Role.name == "Owner"
        )
    )

    db_session.add(
        ScopedRoleAssignment(
            id=uuid.uuid4(),
            membership_id=membership.id,
            role_id=owner_role.id,
            location_id=location.id,
        )
    )
    await db_session.commit()

    response = await client.get(
        f"/api/v1/rooms/?location_id={location.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_forbids_user_without_matching_location(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    token, business, location, membership = await setup_user(db_session)

    owner_role = await db_session.scalar(
        select(Role).where(
            Role.business_id == business.id, Role.name == "Owner"
        )
    )

    # Assign owner role to a different location
    other_location = Location(
        id=uuid.uuid4(), business_id=business.id, name="Other"
    )
    db_session.add(other_location)
    await db_session.flush()

    db_session.add(
        ScopedRoleAssignment(
            id=uuid.uuid4(),
            membership_id=membership.id,
            role_id=owner_role.id,
            location_id=other_location.id,
        )
    )
    await db_session.commit()

    # Requesting without location should be forbidden (no global role)
    response = await client.get(
        "/api/v1/rooms/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403

    # Requesting for the original location (which user doesn't have) should be forbidden
    response = await client.get(
        f"/api/v1/rooms/?location_id={location.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
