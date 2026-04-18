from __future__ import annotations

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.session import get_async_session
from apps.api.app.models.user import User
from apps.api.app.core.security import hash_password

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    job_title: str | None = None
    is_active: bool = True


class UserRead(BaseModel):
    id: str
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    job_title: str | None = None
    is_active: bool
    memberships: list = []


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

    return UserRead(
        id=str(user.id),
        email=user.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        job_title=payload.job_title,
        is_active=user.is_active,
        memberships=[],
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
