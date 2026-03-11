from datetime import datetime

from pydantic import BaseModel

from apps.api.app.models.training import TrainingStatus


class TrainingModuleCreate(BaseModel):
    name: str
    description: str | None = None


class TrainingModuleRead(BaseModel):
    id: str
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class EmployeeTrainingCreate(BaseModel):
    employee_id: str
    module_id: str
    status: TrainingStatus = TrainingStatus.not_started
    score: float | None = None
    completed_at: datetime | None = None


class EmployeeTrainingRead(BaseModel):
    id: str
    employee_id: str
    module_id: str
    status: TrainingStatus
    score: float | None = None

    model_config = {"from_attributes": True}
