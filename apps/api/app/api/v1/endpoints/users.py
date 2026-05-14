from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.session import get_async_session
from apps.api.app.models.user import User
from apps.api.app.core.security import hash_password
from sqlalchemy import select
import uuid

from apps.api.app.models.tenant import Business
from apps.api.app.models.access_control import Membership, Role, ScopedRoleAssignment
from apps.api.app.services.rbac_seed_service import async_seed_default_roles_for_business

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    job_title: str | None = None
    is_active: bool = True
    business_id: str | None = None
    is_owner: bool = False


class UserRead(BaseModel):
    id: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    job_title: str | None = None
    is_active: bool
    memberships: list = []


class InviteRequest(BaseModel):
    email: EmailStr
    role_ids: list[str] = []


@router.post("/invite", status_code=201)
async def invite_user(business_id: str, payload: InviteRequest, session: AsyncSession = Depends(get_async_session)) -> dict:
    """Invite a user to a business. Creates a stub User (status invited) and a Membership with status invited.

    Mirrors the behavior in packages.workforce tenant invite endpoint for administrative flows.
    """
    # Find or create user
    target = await session.scalar(select(User).where(User.email == payload.email))
    if not target:
        # Create a stub user record for invite; keep account inactive until acceptance
        target = User(email=payload.email, hashed_password="", is_active=False)
        session.add(target)
        await session.flush()

    # Validate business exists
    try:
        biz_id = uuid.UUID(business_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid business_id")

    biz = await session.scalar(select(Business).where(Business.id == biz_id))
    if not biz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")

    existing = await session.scalar(select(Membership).where(Membership.user_id == target.id, Membership.business_id == biz.id))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a membership in this business")

    membership = Membership(id=uuid.uuid4(), user_id=target.id, business_id=biz.id, status="invited")
    session.add(membership)
    await session.flush()

    for role_id in payload.role_ids:
        try:
            from apps.api.app.models.access_control import MembershipRole
            session.add(MembershipRole(membership_id=membership.id, role_id=role_id))
        except Exception:
            # If MembershipRole model is not present in this deployment, skip role attachments.
            continue

    await session.commit()
    return {"membership_id": str(membership.id), "user_id": str(target.id), "email": target.email}


@router.post("/", response_model=UserRead, status_code=201)
async def create_user(payload: UserCreate, session: AsyncSession = Depends(get_async_session)) -> UserRead:
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Create a user with an unusable random password; admin should trigger an invite/reset flow separately.
    import secrets

    raw = secrets.token_urlsafe(24)
    user = User(email=payload.email, hashed_password=hash_password(raw), is_active=payload.is_active)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    memberships_out = []

    # If an admin provided a business_id, create an active membership and seed roles
    if payload.business_id is not None:
        # Validate business exists
        try:
            biz_id = uuid.UUID(payload.business_id)
        except Exception:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid business_id")

        biz = await session.scalar(select(Business).where(Business.id == biz_id))
        if biz is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Business not found")

        membership = Membership(id=uuid.uuid4(), user_id=user.id, business_id=biz.id, status="active", is_owner=payload.is_owner)
        session.add(membership)
        await session.flush()

        # Seed default roles for the business if needed and assign Owner role when requested
        await async_seed_default_roles_for_business(session, biz.id)
        owner_role = await session.scalar(select(Role).where(Role.business_id == biz.id, Role.name == "Owner"))
        if payload.is_owner and owner_role is not None:
            scoped = ScopedRoleAssignment(id=uuid.uuid4(), membership_id=membership.id, role_id=owner_role.id, location_id=None)
            session.add(scoped)

        await session.commit()
        memberships_out.append({"business_id": str(biz.id), "status": "active", "is_owner": payload.is_owner})

    return UserRead(
        id=str(user.id),
        email=user.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        job_title=payload.job_title,
        is_active=user.is_active,
        memberships=memberships_out,
    )


@router.get("/")
async def list_users(session: AsyncSession = Depends(get_async_session)) -> dict:
    rows = await session.scalars(select(User))
    users = rows.all()
    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "first_name": None,
                "last_name": None,
                "phone": None,
                "job_title": None,
                "is_active": u.is_active,
                "memberships": [],
            }
            for u in users
        ]
    }
