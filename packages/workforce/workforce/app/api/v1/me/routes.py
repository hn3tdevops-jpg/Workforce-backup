from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.auth_deps import CurrentUser, get_tenant_ctx, _get_user_permissions, _get_user_location_permissions
from apps.api.app.core.db import get_db
from apps.api.app.models.business import Business
from apps.api.app.models.identity import Membership, MembershipStatus

router = APIRouter()


@router.get("/api/v1/me/businesses")
def my_businesses(user: CurrentUser, db: Session = Depends(get_db)):
    """Return businesses the current user is a member of.

    Response: [{id, name, is_default}]
    """
    stmt = select(Business, Membership).join(Membership, Business.id == Membership.business_id).where(
        Membership.user_id == user.id,
        Membership.status == MembershipStatus.active,
    )
    rows = db.execute(stmt).all()
    result = []
    for biz, mem in rows:
        result.append({"id": biz.id, "name": biz.name, "is_default": False})
    return result


@router.get("/api/v1/me/effective-permissions")
def my_effective_permissions(
    user: CurrentUser,
    business_id: str,
    location_id: str | None = None,
    db: Session = Depends(get_db),
):
    """Return computed effective permissions for the current user.

    This is a thin alias around the existing permission resolver so frontend
    callers can fetch the same union used for UI gating.
    """
    if location_id:
        return sorted(_get_user_location_permissions(user, business_id, location_id, db))
    return sorted(_get_user_permissions(user, business_id, db))
