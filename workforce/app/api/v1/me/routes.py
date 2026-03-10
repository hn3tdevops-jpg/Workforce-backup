from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import CurrentUser
from app.core.db import get_db
from app.models.business import Business
from app.models.identity import Membership, MembershipStatus

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
