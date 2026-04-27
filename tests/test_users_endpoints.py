import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    email = f"ui-{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/api/v1/users/",
        json={
            "email": email,
            "first_name": "Test",
            "last_name": "User",
            "phone": "+123",
            "job_title": "Tester",
            "is_active": True,
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == email

    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None


@pytest.mark.asyncio
async def test_create_user_with_membership(client: AsyncClient, db_session: AsyncSession) -> None:
    # Create a tenant and business
    import uuid as _uuid
    from apps.api.app.models.tenant import Tenant, Business, Location
    from apps.api.app.models.access_control import Membership, ScopedRoleAssignment, Role
    from apps.api.app.services.rbac_seed_service import async_seed_default_roles_for_business

    tenant = Tenant(id=_uuid.uuid4(), name="Tenant X", slug=f"tenant-{_uuid.uuid4().hex[:8]}")
    business = Business(id=_uuid.uuid4(), tenant_id=tenant.id, name="Business X")
    location = Location(id=_uuid.uuid4(), business_id=business.id, name="Loc X")

    await db_session.run_sync(lambda sync: sync.add_all([tenant, business, location]))
    await db_session.run_sync(lambda sync: sync.flush())

    email = f"ui-{_uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/api/v1/users/",
        json={
            "email": email,
            "first_name": "Test",
            "last_name": "User",
            "phone": "+123",
            "job_title": "Tester",
            "is_active": True,
            "business_id": str(business.id),
            "is_owner": True,
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == email
    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None

    # Membership should exist
    m = await db_session.scalar(select(Membership).where(Membership.user_id == user.id, Membership.business_id == business.id))
    assert m is not None

    # Owner role assignment should exist
    await async_seed_default_roles_for_business(db_session, business.id)
    owner_role = await db_session.scalar(select(Role).where(Role.business_id == business.id, Role.name == 'Owner'))
    s = await db_session.scalar(select(ScopedRoleAssignment).where(ScopedRoleAssignment.membership_id == m.id, ScopedRoleAssignment.role_id == owner_role.id))
    assert s is not None


@pytest.mark.asyncio
async def test_invite_user_creates_invited_membership(client: AsyncClient, db_session: AsyncSession) -> None:
    import uuid as _uuid
    from apps.api.app.models.tenant import Tenant, Business, Location
    from apps.api.app.models.access_control import Membership

    tenant = Tenant(id=_uuid.uuid4(), name="Tenant Invite", slug=f"tenant-{_uuid.uuid4().hex[:8]}")
    business = Business(id=_uuid.uuid4(), tenant_id=tenant.id, name="Invite Biz")
    await db_session.run_sync(lambda sync: sync.add_all([tenant, business]))
    await db_session.run_sync(lambda sync: sync.flush())

    email = f"invite-{_uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(f"/api/v1/users/invite?business_id={business.id}", json={"email": email, "role_ids": []})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == email

    # Membership should exist with status invited
    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None
    m = await db_session.scalar(select(Membership).where(Membership.user_id == user.id, Membership.business_id == business.id))
    assert m is not None
    assert m.status == 'invited'
