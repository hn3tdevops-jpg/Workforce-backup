from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_session
from apps.api.app.models.scheduling import AvailabilityBlock, Shift
from apps.api.app.schemas.scheduling import (
    AvailabilityBlockCreate,
    AvailabilityBlockRead,
    CandidateRead,
    ShiftCreate,
    ShiftRead,
)
from apps.api.app.services.audit import log_change
from apps.api.app.services.matching import find_candidates_for_shift

router = APIRouter(tags=["scheduling"])


@router.post("/availability", response_model=AvailabilityBlockRead, status_code=201)
def create_availability(payload: AvailabilityBlockCreate, db: Session = Depends(get_session)):
    obj = AvailabilityBlock(
        employee_id=payload.employee_id,
        start_ts=payload.start_ts,
        end_ts=payload.end_ts,
        status=payload.status,
    )
    db.add(obj)
    db.flush()
    log_change(
        db, "api", None, "AvailabilityBlock", obj.id, "create", None,
        payload.model_dump(mode="json"),
    )
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/shifts", response_model=ShiftRead, status_code=201)
def create_shift(payload: ShiftCreate, db: Session = Depends(get_session)):
    obj = Shift(
        business_id=payload.business_id,
        location_id=payload.location_id,
        role_id=payload.role_id,
        start_ts=payload.start_ts,
        end_ts=payload.end_ts,
        needed_count=payload.needed_count,
        status=payload.status,
    )
    db.add(obj)
    db.flush()
    log_change(
        db, "api", None, "Shift", obj.id, "create", None, payload.model_dump(mode="json")
    )
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/shifts/{shift_id}/candidates", response_model=list[CandidateRead])
def get_candidates(shift_id: str, db: Session = Depends(get_session)):
    try:
        candidates = find_candidates_for_shift(db, shift_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    return candidates
