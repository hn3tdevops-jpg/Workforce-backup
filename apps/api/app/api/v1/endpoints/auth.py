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


class SwitchBusinessRequest(BaseModel):
    business_id: uuid.UUID


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


class SwitchBusinessResponse(BaseModel):
    access_token: str
    token_type: str
    business_id: uuid.UUID
    roles: list[str]
    permissions: list[str]


class MeResponse(BaseModel):
    user: UserSummary
    business_id: uuid.UUID
    memberships: list[MembershipSummary]
    roles: list[str]
    permissions: list[str]


async def _load_active_memberships(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[Membership]:
    return await session.run_sync(
        lambda sync_session: get_active_memberships_for_user(sync_session, user_id)
    )


def _choose_membership(
    memberships: list[Membership],
    requested_business_id: uuid.UUID | None,
    user: User,
) -> Membership:
    chosen_membership = None

    if requested_business_id is not None:
        for membership in memberships:
            if membership.business_id == requested_business_id:
                chosen_membership = membership
                break
        if chosen_membership is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to that business.",
            )
        return chosen_membership

    if user.business_id is not None:
        for membership in memberships:
            if membership.business_id == user.business_id:
                chosen_membership = membership
                break

    if chosen_membership is None:
        chosen_membership = memberships[0]

    return chosen_membership


async def _load_roles_and_permissions(
    session: AsyncSession,
    user_id: uuid.UUID,
    business_id: uuid.UUID,
) -> tuple[list[str], list[str]]:
    roles = sorted(
        await session.run_sync(
            lambda sync_session: get_effective_role_names(
                sync_session,
                user_id,
                business_id,
                None,
            )
        )
    )
    permissions = sorted(
        await session.run_sync(
            lambda sync_session: get_effective_permission_codes(
                sync_session,
                user_id,
                business_id,
                None,
            )
        )
    )
    return roles, permissions


async def _load_membership_summaries(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[MembershipSummary]:
    memberships = (
        await session.scalars(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.status == "active",
            )
        )
    ).all()

    return [
        MembershipSummary(
            business_id=m.business_id,
            status=m.status,
            is_owner=m.is_owner,
        )
        for m in memberships
    ]


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

    memberships = await _load_active_memberships(session, user.id)
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active memberships.",
        )

    chosen_membership = _choose_membership(memberships, payload.business_id, user)

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


@router.post("/switch-business", response_model=SwitchBusinessResponse)
async def switch_business(
    payload: SwitchBusinessRequest,
    auth: AuthContext = Depends(get_current_auth_context),
    session: AsyncSession = Depends(get_async_session),
) -> SwitchBusinessResponse:
    memberships = await _load_active_memberships(session, auth.user_id)
    chosen_membership = _choose_membership(memberships, payload.business_id, auth.user)

    access_token = create_access_token(
        user_id=str(auth.user_id),
        business_id=str(chosen_membership.business_id),
    )

    roles, permissions = await _load_roles_and_permissions(
        session,
        auth.user_id,
        chosen_membership.business_id,
    )

    return SwitchBusinessResponse(
        access_token=access_token,
        token_type="bearer",
        business_id=chosen_membership.business_id,
        roles=roles,
        permissions=permissions,
    )


@router.get("/me", response_model=MeResponse)
async def me(
    auth: AuthContext = Depends(get_current_auth_context),
    session: AsyncSession = Depends(get_async_session),
) -> MeResponse:
    memberships = await _load_membership_summaries(session, auth.user_id)
    roles, permissions = await _load_roles_and_permissions(
        session,
        auth.user_id,
        auth.business_id,
    )

    return MeResponse(
        user=UserSummary(
            id=auth.user.id,
            email=auth.user.email,
            is_active=auth.user.is_active,
        ),
        business_id=auth.business_id,
        memberships=memberships,
        roles=roles,
        permissions=permissions,
    )