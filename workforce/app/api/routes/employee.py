from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.models.business import Business
from app.models.employee import Employee, EmployeeRole, Employment
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeRead,
    EmployeeRoleCreate,
    EmployeeRoleRead,
    EmploymentCreate,
    EmploymentRead,
)
from app.services.audit import log_change

router = APIRouter(tags=["employees"])


@router.post("/employees", response_model=EmployeeRead, status_code=201)
def create_employee(payload: EmployeeCreate, db: Session = Depends(get_session)):
    obj = Employee(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
    )
    db.add(obj)
    db.flush()
    log_change(db, "api", None, "Employee", obj.id, "create", None, payload.model_dump())
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/businesses/{business_id}/employments", response_model=EmploymentRead, status_code=201)
def create_employment(
    business_id: str, payload: EmploymentCreate, db: Session = Depends(get_session)
):
    if not db.get(Business, business_id):
        raise HTTPException(404, "Business not found")
    if not db.get(Employee, payload.employee_id):
        raise HTTPException(404, "Employee not found")
    obj = Employment(
        business_id=business_id,
        employee_id=payload.employee_id,
        status=payload.status,
        hire_date=payload.hire_date,
    )
    db.add(obj)
    db.flush()
    log_change(
        db, "api", None, "Employment", obj.id, "create", None,
        {"business_id": business_id, "employee_id": payload.employee_id, "status": payload.status},
    )
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/employments/{employment_id}/roles", response_model=EmployeeRoleRead, status_code=201)
def assign_role(
    employment_id: str, payload: EmployeeRoleCreate, db: Session = Depends(get_session)
):
    emp = db.get(Employment, employment_id)
    if not emp:
        raise HTTPException(404, "Employment not found")
    obj = EmployeeRole(
        employment_id=employment_id,
        role_id=payload.role_id,
        proficiency=payload.proficiency,
    )
    db.add(obj)
    db.flush()
    log_change(
        db, "api", None, "EmployeeRole", obj.id, "create", None,
        {"employment_id": employment_id, "role_id": payload.role_id, "proficiency": payload.proficiency},
    )
    db.commit()
    db.refresh(obj)
    return obj
