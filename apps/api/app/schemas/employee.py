from __future__ import annotations

import uuid
from pydantic import BaseModel, EmailStr


class EmployeeCreate(BaseModel):
    business_id: uuid.UUID
    location_id: uuid.UUID | None = None
    first_name: str | None = None
    last_name: str | None = None
    external_id: str | None = None
    email_work: EmailStr | None = None


class EmployeeRead(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    location_id: uuid.UUID | None = None
    first_name: str | None = None
    last_name: str | None = None
    email_work: EmailStr | None = None
    is_active: bool


class UserEmployeeLinkCreate(BaseModel):
    employee_id: uuid.UUID


class UserEmployeeLinkRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    employee_id: uuid.UUID
    business_id: uuid.UUID
    is_active: bool
    created_at: str | None = None
