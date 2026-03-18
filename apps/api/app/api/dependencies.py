from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_async_session
from app.models.user import User
from app.services.rbac_service import user_has_permission

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user: User
    user_id: uuid.UUID
    business_id: uuid.UUID
    claims: dict


async def get_current_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_async_session),
) -> AuthContext:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    try:
        claims = decode_access_token(credentials.credentials)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token.",
        ) from exc

    sub = claims.get("sub")
    business_id_raw = claims.get("business_id")

    if not sub or not business_id_raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing required claims.",
        )

    try:
        user_id = uuid.UUID(str(sub))
        business_id = uuid.UUID(str(business_id_raw))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token contains invalid identifiers.",
        ) from exc

    user = await session.scalar(
        select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
        )
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user was not found.",
        )

    return AuthContext(
        user=user,
        user_id=user_id,
        business_id=business_id,
        claims=claims,
    )


def require_permission(permission_code: str):
    async def dependency(
        auth: AuthContext = Depends(get_current_auth_context),
        session: AsyncSession = Depends(get_async_session),
    ) -> AuthContext:
        allowed = await session.run_sync(
            lambda sync_session: user_has_permission(
                sync_session,
                auth.user_id,
                permission_code,
                auth.business_id,
                None,
            )
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions.",
            )
        return auth

    return dependency