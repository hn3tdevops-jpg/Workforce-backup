from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.models.business import Business, Location
from app.schemas.business import (
    BusinessCreate, BusinessRead,
    LocationCreate, LocationRead, LocationWithChildrenRead,
)
from app.services.audit import log_change

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post("", response_model=BusinessRead, status_code=201)
def create_business(payload: BusinessCreate, db: Session = Depends(get_session)):
    obj = Business(name=payload.name)
    db.add(obj)
    db.flush()
    log_change(db, "api", None, "Business", obj.id, "create", None, {"name": obj.name})
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/{business_id}/locations", response_model=LocationRead, status_code=201)
def create_location(
    business_id: str, payload: LocationCreate, db: Session = Depends(get_session)
):
    biz = db.get(Business, business_id)
    if not biz:
        raise HTTPException(404, "Business not found")
    if payload.parent_id:
        parent = db.get(Location, payload.parent_id)
        if not parent or parent.business_id != business_id:
            raise HTTPException(404, "Parent location not found in this business")
    obj = Location(
        business_id=business_id,
        name=payload.name,
        timezone=payload.timezone,
        parent_id=payload.parent_id,
    )
    db.add(obj)
    db.flush()
    log_change(
        db, "api", None, "Location", obj.id, "create", None,
        {"business_id": business_id, "name": obj.name, "timezone": obj.timezone,
         "parent_id": obj.parent_id},
    )
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{business_id}/locations", response_model=list[LocationWithChildrenRead])
def list_locations(business_id: str, db: Session = Depends(get_session)):
    """Return root locations (parent_id=None) with their children nested."""
    roots = db.execute(
        select(Location).where(
            Location.business_id == business_id,
            Location.parent_id.is_(None),
        )
    ).scalars().all()
    return roots


@router.post(
    "/{business_id}/locations/{location_id}/sub-locations",
    response_model=LocationRead, status_code=201,
)
def create_sub_location(
    business_id: str, location_id: str, payload: LocationCreate,
    db: Session = Depends(get_session),
):
    biz = db.get(Business, business_id)
    if not biz:
        raise HTTPException(404, "Business not found")
    parent = db.get(Location, location_id)
    if not parent or parent.business_id != business_id:
        raise HTTPException(404, "Parent location not found")
    obj = Location(
        business_id=business_id,
        name=payload.name,
        timezone=payload.timezone,
        parent_id=location_id,
    )
    db.add(obj)
    db.flush()
    log_change(
        db, "api", None, "Location", obj.id, "create", None,
        {"business_id": business_id, "name": obj.name, "parent_id": location_id},
    )
    db.commit()
    db.refresh(obj)
    return obj


@router.get(
    "/{business_id}/locations/{location_id}/sub-locations",
    response_model=list[LocationRead],
)
def list_sub_locations(
    business_id: str, location_id: str, db: Session = Depends(get_session)
):
    parent = db.get(Location, location_id)
    if not parent or parent.business_id != business_id:
        raise HTTPException(404, "Location not found")
    return db.execute(
        select(Location).where(Location.parent_id == location_id)
    ).scalars().all()
