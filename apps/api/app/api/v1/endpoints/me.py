from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth_context
from app.db.session import get_async_session
from app.models.tenant import Business
from app.models.access_control import Membership, ScopedRoleAssignment

router = APIRouter()


@router.get("/businesses")
async def my_businesses(auth = Depends(get_current_auth_context), session: AsyncSession = Depends(get_async_session)):
    businesses = {}

    # Try membership-based lookup
    try:
        stmt = select(Business).join(Membership, Business.id == Membership.business_id).where(
            Membership.user_id == auth.user_id,
            Membership.status == "active",
        )
        result = await session.execute(stmt)
        for biz in result.scalars().unique():
            businesses[str(biz.id)] = {"id": str(biz.id), "name": biz.name, "is_default": False}
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
            businesses[str(biz.id)] = {"id": str(biz.id), "name": biz.name, "is_default": False}
    except OperationalError:
        pass

    return list(businesses.values())
