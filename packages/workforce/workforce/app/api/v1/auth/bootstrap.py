"""
Bootstrap endpoint — creates the initial superadmin account.

This endpoint is protected by two guards:
  1. ``ENABLE_BOOTSTRAP`` setting must be ``True`` (env var).
  2. The ``X-Bootstrap-Token`` request header must match ``BOOTSTRAP_TOKEN`` setting.

It also verifies the database contains **zero** users before proceeding, so it
can only be called once on a fresh installation.

Operator usage
--------------
::

    export ENABLE_BOOTSTRAP=true
    export BOOTSTRAP_TOKEN="$(openssl rand -hex 24)"
    curl -X POST http://localhost:8000/api/v1/auth/bootstrap \\
         -H "Content-Type: application/json" \\
         -H "X-Bootstrap-Token: $BOOTSTRAP_TOKEN" \\
         -d '{"email":"admin@example.com","password":"ChangeMeNow!"}'

**Disable ENABLE_BOOTSTRAP after the initial superadmin has been created.**
"""

import secrets as _secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.app.core.config import settings
from apps.api.app.core.db import get_db
from apps.api.app.core.security import hash_password
from apps.api.app.models.identity import User, UserStatus

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class BootstrapRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    first_name: str | None = None
    last_name: str | None = None


@router.post("/bootstrap", status_code=201)
def bootstrap(
    payload: BootstrapRequest,
    x_bootstrap_token: str | None = Header(None, alias="X-Bootstrap-Token"),
    db: Session = Depends(get_db),
):
    """Create the initial superadmin account (one-time, guarded by feature flag and token)."""

    if not settings.ENABLE_BOOTSTRAP:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bootstrap disabled")

    if not settings.BOOTSTRAP_TOKEN or not _secrets.compare_digest(
        x_bootstrap_token or "", settings.BOOTSTRAP_TOKEN
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing or invalid bootstrap token")

    count: int = db.execute(select(func.count()).select_from(User)).scalar_one()
    if count > 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Bootstrap already performed")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_superadmin=True,
        status=UserStatus.active,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"id": user.id, "email": user.email}
