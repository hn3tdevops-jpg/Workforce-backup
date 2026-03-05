from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.models.training import EmployeeTraining, TrainingModule
from app.schemas.training import (
    EmployeeTrainingCreate,
    EmployeeTrainingRead,
    TrainingModuleCreate,
    TrainingModuleRead,
)
from app.services.audit import log_change

router = APIRouter(tags=["training"])


@router.post("/training/modules", response_model=TrainingModuleRead, status_code=201)
def create_module(payload: TrainingModuleCreate, db: Session = Depends(get_session)):
    obj = TrainingModule(name=payload.name, description=payload.description)
    db.add(obj)
    db.flush()
    log_change(db, "api", None, "TrainingModule", obj.id, "create", None, payload.model_dump())
    db.commit()
    db.refresh(obj)
    return obj


@router.post("/training/records", response_model=EmployeeTrainingRead, status_code=201)
def create_training_record(payload: EmployeeTrainingCreate, db: Session = Depends(get_session)):
    obj = EmployeeTraining(
        employee_id=payload.employee_id,
        module_id=payload.module_id,
        status=payload.status,
        score=payload.score,
        completed_at=payload.completed_at,
    )
    db.add(obj)
    db.flush()
    log_change(
        db, "api", None, "EmployeeTraining", obj.id, "create", None, payload.model_dump(mode="json")
    )
    db.commit()
    db.refresh(obj)
    return obj
