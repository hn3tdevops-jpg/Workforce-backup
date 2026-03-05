from datetime import datetime

from pydantic import BaseModel

from app.models.scheduling import AvailabilityStatus, ShiftStatus


class AvailabilityBlockCreate(BaseModel):
    employee_id: str
    start_ts: datetime
    end_ts: datetime
    status: AvailabilityStatus = AvailabilityStatus.available


class AvailabilityBlockRead(BaseModel):
    id: str
    employee_id: str
    start_ts: datetime
    end_ts: datetime
    status: AvailabilityStatus

    model_config = {"from_attributes": True}


class ShiftCreate(BaseModel):
    business_id: str
    location_id: str
    role_id: str
    start_ts: datetime
    end_ts: datetime
    needed_count: int = 1
    status: ShiftStatus = ShiftStatus.draft


class ShiftRead(BaseModel):
    id: str
    business_id: str
    location_id: str
    role_id: str
    start_ts: datetime
    end_ts: datetime
    needed_count: int
    status: ShiftStatus

    model_config = {"from_attributes": True}


class CandidateRead(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: str | None = None
    proficiency: int
    availability_status: AvailabilityStatus
