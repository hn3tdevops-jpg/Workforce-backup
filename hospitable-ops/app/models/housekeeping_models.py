from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from app.db.session import Base
import enum
import datetime

class UnitStatus(enum.Enum):
    DIRTY = 'DIRTY'
    ASSIGNED = 'ASSIGNED'
    IN_PROGRESS = 'IN_PROGRESS'
    CLEANED = 'CLEANED'
    INSPECTED = 'INSPECTED'
    READY = 'READY'

class TaskStatus(enum.Enum):
    OPEN = 'OPEN'
    ASSIGNED = 'ASSIGNED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    INSPECTED = 'INSPECTED'
    CANCELED = 'CANCELED'

class Unit(Base):
    __tablename__ = 'units'
    id = Column(String, primary_key=True)
    location_id = Column(String, nullable=False)
    label = Column(String, nullable=False)
    type = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    status = Column(Enum(UnitStatus), default=UnitStatus.DIRTY)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(String, primary_key=True)
    location_id = Column(String, nullable=False)
    unit_id = Column(String, ForeignKey('units.id'))
    date = Column(String, nullable=False)
    type = Column(String, nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.OPEN)
    assigned_external_employee_id = Column(String, nullable=True)
    external_shift_id = Column(String, nullable=True)
    due_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
