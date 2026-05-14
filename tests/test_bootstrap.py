import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.access_control import Membership, Role, ScopedRoleAssignment
from app.models.tenant import Business, Location, Tenant
from app.models.user import User


@pytest.mark.asyncio
async def test_bootstrap_creates_entities(
    client: AsyncClient, db_session
) -> None:
    response = await client.post(
        "/api/v1/bootstrap",
        json={
            "admin_email": "hn3torg@gmail.com",
            "admin_password": "BootstrapPass1!",
            "business_name": "HN3T Org",
            "location_name": "HQ",
        },
    )
    assert response.status_code == 201, response.text

    data = response.json()
    business_id = uuid.UUID(data["business_id"])
    location_id = uuid.UUID(data["location_id"])
    user_id = uuid.UUID(data["user_id"])

    business = await db_session.scalar(
        select(Business).where(Business.id == business_id)
    )
    location = await db_session.scalar(
        select(Location).where(Location.id == location_id)
    )
    user = await db_session.scalar(select(User).where(User.id == user_id))

    assert business is not None
    assert location is not None
    assert user is not None

    assert business.name == "HN3T Org"
    assert location.name == "HQ"
    assert location.business_id == business.id
    assert user.email == "hn3torg@gmail.com"
    assert user.business_id == business.id

    tenant = await db_session.scalar(
        select(Tenant).where(Tenant.id == business.tenant_id)
    )
    assert tenant is not None
    assert tenant.name == "HN3T Org"

    membership = await db_session.scalar(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.business_id == business.id,
        )
    )
    assert membership is not None
    assert membership.status == "active"
    assert membership.is_owner is True

    owner_role = await db_session.scalar(
        select(Role).where(
            Role.business_id == business.id,
            Role.name == "Owner",
        )
    )
    assert owner_role is not None

    owner_assignment = await db_session.scalar(
        select(ScopedRoleAssignment).where(
            ScopedRoleAssignment.membership_id == membership.id,
            ScopedRoleAssignment.role_id == owner_role.id,
            ScopedRoleAssignment.location_id.is_(None),
        )
    )
    assert owner_assignment is not None

    roles = (
        await db_session.scalars(
            select(Role).where(Role.business_id == business.id)
        )
    ).all()
    assert {role.name for role in roles} == {
        "Owner",
        "Admin",
        "Manager",
        "Supervisor",
        "Staff",
    }


@pytest.mark.asyncio
async def test_bootstrap_forbidden_when_users_exist(
    client: AsyncClient,
) -> None:
    first = await client.post(
        "/api/v1/bootstrap",
        json={
            "admin_email": "first@example.com",
            "admin_password": "BootstrapPass1!",
            "business_name": "First Org",
            "location_name": "HQ",
        },
    )
    assert first.status_code == 201, first.text

    second = await client.post(
        "/api/v1/bootstrap",
        json={
            "admin_email": "second@example.com",
            "admin_password": "AnotherPass1!",
            "business_name": "Another Org",
            "location_name": "Branch",
        },
    )
    assert second.status_code == 403
    assert (
        second.json()["detail"]
        == "Bootstrap is only allowed when no users exist."
    )
