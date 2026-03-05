from datetime import date

from pydantic import BaseModel

from app.models.employee import EmploymentStatus


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None


class EmployeeRead(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None

    model_config = {"from_attributes": True}


class EmploymentCreate(BaseModel):
    employee_id: str
    status: EmploymentStatus = EmploymentStatus.active
    hire_date: date | None = None


class EmploymentRead(BaseModel):
    id: str
    business_id: str
    employee_id: str
    status: EmploymentStatus

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    name: str


class RoleRead(BaseModel):
    id: str
    name: str

    model_config = {"from_attributes": True}


class EmployeeRoleCreate(BaseModel):
    role_id: str
    proficiency: int = 3


class EmployeeRoleRead(BaseModel):
    id: str
    employment_id: str
    role_id: str
    proficiency: int

    model_config = {"from_attributes": True}
