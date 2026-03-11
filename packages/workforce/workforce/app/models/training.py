import enum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.models.base import Base, TimestampMixin, UUIDMixin


class TrainingStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class TrainingModule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "training_modules"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)


class EmployeeTraining(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employee_trainings"

    employee_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    module_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("training_modules.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[TrainingStatus] = mapped_column(
        Enum(TrainingStatus, name="training_status"),
        nullable=False,
        default=TrainingStatus.not_started,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    completed_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("employee_id", "module_id", name="uq_employee_training"),
    )
