from fastapi import APIRouter, Depends
from typing import List
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth_context
from app.db.session import get_async_session
from app.models.tenant import Business
from app.models.access_control import Membership, ScopedRoleAssignment
from app.services.rbac_service import get_effective_permission_codes


class BusinessSelector(BaseModel):
    id: str
    name: str
    is_default: bool


router = APIRouter()


@router.get("/businesses", response_model=List[BusinessSelector])
async def my_businesses(auth = Depends(get_current_auth_context), session: AsyncSession = Depends(get_async_session)):
    """Return businesses the current user belongs to.

    The response includes an `is_default` flag derived from the business_id in the
    authenticated token (current active business for the session).
    """
    businesses: dict[str, dict] = {}

    token_business_id = str(getattr(auth, "business_id", ""))

    # Try membership-based lookup
    try:
        stmt = select(Business).join(Membership, Business.id == Membership.business_id).where(
            Membership.user_id == auth.user_id,
            Membership.status == "active",
        )
        result = await session.execute(stmt)
        for biz in result.scalars().unique():
            businesses[str(biz.id)] = {"id": str(biz.id), "name": biz.name, "is_default": (str(biz.id) == token_business_id)}
    except OperationalError:
        pass

    # Fallback via scoped role assignments -> membership -> business
    try:
        stmt2 = (
            select(Business)
            .join(Membership, Business.id == Membership.business_id)
            .join(ScopedRoleAssignment, ScopedRoleAssignment.membership_id == Membership.id)
            .where(Membership.user_id == auth.user_id)
        )
        result2 = await session.execute(stmt2)
        for biz in result2.scalars().unique():
            businesses[str(biz.id)] = {"id": str(biz.id), "name": biz.name, "is_default": (str(biz.id) == token_business_id)}
    except OperationalError:
        pass

    return list(businesses.values())


@router.get("/effective-permissions")
async def my_effective_permissions(
    auth = Depends(get_current_auth_context),
    session: AsyncSession = Depends(get_async_session),
    business_id: str | None = None,
    location_id: str | None = None,
):
    """Return the current user's effective permission codes for the active business.

    `business_id` is accepted for compatibility with existing callers; when
    provided it must match the active business in the auth context.
    """
    if business_id is not None and str(business_id) != str(auth.business_id):
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Business mismatch.")

    permissions = await session.run_sync(
        lambda sync_session: get_effective_permission_codes(
            sync_session,
            auth.user_id,
            auth.business_id,
            location_id,
        )
    )
    return sorted(permissions)
