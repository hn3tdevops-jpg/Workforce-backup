"""
Auth routes: login, refresh, register (superadmin only for now).
"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import CurrentUser
from app.core.db import get_db
from app.core.security import (
    create_access_token, create_refresh_token,
    hash_password, hash_refresh_token, verify_password,
)
from app.core.config import settings
from app.models.identity import RefreshToken, User, UserStatus

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/token", response_model=TokenResponse)
def token(payload: LoginRequest, db: Session = Depends(get_db)):
    """OAuth2-style token endpoint (alias for /login)."""
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if user.status != UserStatus.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account inactive")

    access = create_access_token(user.id, user.is_superadmin)
    raw_refresh, refresh_hash = create_refresh_token()

    rt = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rt)
    db.commit()
    expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    return TokenResponse(access_token=access, refresh_token=raw_refresh, expires_in=expires_in)


@router.post("/logout", status_code=200)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)):
    """Revoke a refresh token (logout)."""
    token_hash = hash_refresh_token(payload.refresh_token)
    rt = db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            ~RefreshToken.revoked,
        )
    ).scalar_one_or_none()
    if rt:
        rt.revoked = True
        db.commit()
    return {"detail": "logged out"}


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "Email already registered")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_superadmin=False,
        status=UserStatus.active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    if user.status != UserStatus.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account inactive")

    access = create_access_token(user.id, user.is_superadmin)
    raw_refresh, refresh_hash = create_refresh_token()

    rt = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(rt)
    db.commit()
    return TokenResponse(access_token=access, refresh_token=raw_refresh)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_hash = hash_refresh_token(payload.refresh_token)
    rt = db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
        )
    ).scalar_one_or_none()
    if not rt:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or revoked refresh token")

    exp = rt.expires_at
    if isinstance(exp, str):
        exp = datetime.fromisoformat(exp)
    # Ensure timezone-aware comparison (SQLite may return naive datetimes)
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=timezone.utc)
    if exp < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token expired")

    # Rotate: revoke old, issue new
    rt.revoked = True
    user = db.get(User, rt.user_id)
    access = create_access_token(user.id, user.is_superadmin)
    raw_new, new_hash = create_refresh_token()
    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        revoked=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(new_rt)
    db.commit()
    return TokenResponse(access_token=access, refresh_token=raw_new)


@router.get("/me")
def me(user: CurrentUser):
    return {"id": user.id, "email": user.email, "is_superadmin": user.is_superadmin}
