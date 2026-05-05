from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import AuthContext, get_current_auth_context
from apps.api.app.core.security import create_access_token, verify_password, hash_password
from apps.api.app.db.session import get_async_session
from apps.api.app.models.access_control import Membership
from apps.api.app.models.user import User
from apps.api.app.services.rbac_service import (
    get_active_memberships_for_user,
    get_effective_permission_codes,
    get_effective_role_names,
)

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    access_token: str | None = None
    token_type: str | None = None
    user: UserSummary | None = None
    business_id: uuid.UUID | None = None



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


class AccessContextAssignment(BaseModel):
    user_id: uuid.UUID
    business_id: uuid.UUID


class AccessContextScope(BaseModel):
    roles: list[str]
    permissions: list[str]


class AccessContextResponse(BaseModel):
    assignment: AccessContextAssignment
    scope: AccessContextScope
    compat: str


async def _load_active_memberships(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> list[Membership]:
    memberships = await session.run_sync(
        lambda sync_session: get_active_memberships_for_user(sync_session, user_id)
    )
    return memberships


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

    user_business_id = getattr(user, "business_id", None)
    if user_business_id is not None:
        for membership in memberships:
            if membership.business_id == user_business_id:
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


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RegisterResponse:
    """Create a new system user (self-registration).

    Minimal, safe implementation: rejects duplicate emails and stores a bcrypt-hashed password.
    This keeps the user model separate from employee files and preserves tenant scoping.
    Additionally, issue an access token for immediate login in dev/UX scenarios.
    """
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered.")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Issue an access token without a chosen business; frontend will decide how to proceed.
    access_token = create_access_token(user_id=str(user.id))
    user_summary = UserSummary(id=user.id, email=user.email, is_active=user.is_active)

    return RegisterResponse(
        id=user.id,
        email=user.email,
        access_token=access_token,
        token_type="bearer",
        user=user_summary,
        business_id=None,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> LoginResponse:
    """Authenticate a user and return an access token.

    NOTE: Database access errors are caught and converted to a 503 so the frontend
    receives a stable, non-exposing error message instead of an internal traceback.
    This is a minimal safe mitigation for production environments where migrations
    or DB provisioning may be incomplete. Operators should run migrations/seed in
    production to fully restore auth functionality.
    """
    try:
        user = await session.scalar(
            select(User).where(User.email == payload.email)
        )

        # DEBUG: show hashed password and verification result when running tests

        valid_pw = user is not None and verify_password(payload.password, user.hashed_password)
        if user is None or not valid_pw:
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

    except HTTPException:
        # Re-raise expected HTTP exceptions (401/403)
        raise
    except Exception:  # pragma: no cover - defensive
        import logging

        logging.exception("Unhandled error in /auth/login")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable.",
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


@router.get("/me/access-context", response_model=AccessContextResponse)
async def me_access_context(
    auth: AuthContext = Depends(get_current_auth_context),
    session: AsyncSession = Depends(get_async_session),
) -> AccessContextResponse:
    """Return the effective access context for the authenticated user.

    Resolves roles and permissions from the canonical RBAC model for the
    user's current business scope. Returns a single COMPAT scope string
    that summarises the active context without exposing internal identifiers
    beyond what is already present in the bearer token claims.
    """
    memberships = await session.run_sync(
        lambda sync_session: get_active_memberships_for_user(sync_session, auth.user_id)
    )
    active_for_business = [m for m in memberships if m.business_id == auth.business_id]
    if not active_for_business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active membership for the current business context.",
        )

    roles, permissions = await _load_roles_and_permissions(
        session,
        auth.user_id,
        auth.business_id,
    )

    compat = f"COMPAT:user={auth.user_id}:business={auth.business_id}"

    return AccessContextResponse(
        assignment=AccessContextAssignment(
            user_id=auth.user_id,
            business_id=auth.business_id,
        ),
        scope=AccessContextScope(
            roles=roles,
            permissions=permissions,
        ),
        compat=compat,
    )
