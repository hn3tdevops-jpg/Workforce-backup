from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import get_async_session
from app.models.access_control import Membership, Role, ScopedRoleAssignment
from app.models.tenant import Business, Location, Tenant
from app.models.user import User
from app.services.rbac_seed_service import async_seed_default_roles_for_business

router = APIRouter()


class BootstrapRequest(BaseModel):
    admin_email: EmailStr
    admin_password: str
    business_name: str
    location_name: str


class BootstrapResponse(BaseModel):
    business_id: uuid.UUID
    location_id: uuid.UUID
    user_id: uuid.UUID


def _slugify(value: str) -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or f"tenant-{uuid.uuid4().hex[:8]}"


@router.post("", response_model=BootstrapResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap(
    payload: BootstrapRequest,
    session: AsyncSession = Depends(get_async_session),
) -> BootstrapResponse:
    user_count = await session.scalar(select(func.count()).select_from(User))
    if (user_count or 0) > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bootstrap is only allowed when no users exist.",
        )

    tenant = Tenant(
        id=uuid.uuid4(),
        name=payload.business_name,
        slug=_slugify(payload.business_name),
    )
    session.add(tenant)
    await session.flush()

    business = Business(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        name=payload.business_name,
    )
    session.add(business)
    await session.flush()

    location = Location(
        id=uuid.uuid4(),
        business_id=business.id,
        name=payload.location_name,
    )
    session.add(location)
    await session.flush()

    user = User(
        id=uuid.uuid4(),
        email=payload.admin_email,
        hashed_password=hash_password(payload.admin_password),
        business_id=business.id,  # transitional compatibility field
        is_active=True,
    )
    session.add(user)
    await session.flush()

    membership = Membership(
        id=uuid.uuid4(),
        user_id=user.id,
        business_id=business.id,
        status="active",
        is_owner=True,
    )
    session.add(membership)
    await session.flush()

    await async_seed_default_roles_for_business(session, business.id)

    owner_role = await session.scalar(
        select(Role).where(Role.business_id == business.id, Role.name == "Owner")
    )
    if owner_role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Owner role was not created during bootstrap.",
        )

    session.add(
        ScopedRoleAssignment(
            id=uuid.uuid4(),
            membership_id=membership.id,
            role_id=owner_role.id,
            location_id=None,
        )
    )

    await session.commit()

    return BootstrapResponse(
        business_id=business.id,
        location_id=location.id,
        user_id=user.id,
    )