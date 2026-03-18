from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AuthContext, get_current_auth_context
from app.core.security import create_access_token, verify_password
from app.db.session import get_async_session
from app.models.access_control import Membership
from app.models.user import User
from app.services.rbac_service import (
    get_active_memberships_for_user,
    get_effective_permission_codes,
    get_effective_role_names,
)

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    business_id: uuid.UUID | None = None


class UserSummary(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool


class MembershipSummary(BaseModel):
    business_id: uuid.UUID
    status: str
    is_owner: bool


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    business_id: uuid.UUID
    user: UserSummary


class MeResponse(BaseModel):
    user: UserSummary
    business_id: uuid.UUID
    memberships: list[MembershipSummary]
    roles: list[str]
    permissions: list[str]


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> LoginResponse:
    user = await session.scalar(
        select(User).where(User.email == payload.email)
    )
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user.",
        )

    memberships = await session.run_sync(
        lambda sync_session: get_active_memberships_for_user(sync_session, user.id)
    )
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active memberships.",
        )

    chosen_membership = None
    if payload.business_id is not None:
        for membership in memberships:
            if membership.business_id == payload.business_id:
                chosen_membership = membership
                break
        if chosen_membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to that business.",
            )
    else:
        if user.business_id is not None:
            for membership in memberships:
                if membership.business_id == user.business_id:
                    chosen_membership = membership
                    break
        if chosen_membership is None:
            chosen_membership = memberships[0]

    access_token = create_access_token(
        user_id=str(user.id),
        business_id=str(chosen_membership.business_id),
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        business_id=chosen_membership.business_id,
        user=UserSummary(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
        ),
    )


@router.get("/me", response_model=MeResponse)
async def me(
    auth: AuthContext = Depends(get_current_auth_context),
    session: AsyncSession = Depends(get_async_session),
) -> MeResponse:
    memberships = (
        await session.scalars(
            select(Membership).where(
                Membership.user_id == auth.user_id,
                Membership.status == "active",
            )
        )
    ).all()

    roles = sorted(
        await session.run_sync(
            lambda sync_session: get_effective_role_names(
                sync_session,
                auth.user_id,
                auth.business_id,
                None,
            )
        )
    )

    permissions = sorted(
        await session.run_sync(
            lambda sync_session: get_effective_permission_codes(
                sync_session,
                auth.user_id,
                auth.business_id,
                None,
            )
        )
    )

    return MeResponse(
        user=UserSummary(
            id=auth.user.id,
            email=auth.user.email,
            is_active=auth.user.is_active,
        ),
        business_id=auth.business_id,
        memberships=[
            MembershipSummary(
                business_id=m.business_id,
                status=m.status,
                is_owner=m.is_owner,
            )
            for m in memberships
        ],
        roles=roles,
        permissions=permissions,
    )