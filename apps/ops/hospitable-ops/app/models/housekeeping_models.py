from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Boolean, Text
from apps.api.app.db.session import Base
import enum
import datetime

class UnitStatus(enum.Enum):
    DIRTY = 'DIRTY'
    ASSIGNED = 'ASSIGNED'
    IN_PROGRESS = 'IN_PROGRESS'
    CLEANED = 'CLEANED'
    INSPECTED = 'INSPECTED'
    READY = 'READY'
    OUT_OF_ORDER = 'OUT_OF_ORDER'
    DND = 'DND'
    LATE_CHECKOUT = 'LATE_CHECKOUT'
    MAINTENANCE_HOLD = 'MAINTENANCE_HOLD'


class IssueStatus(enum.Enum):
    OPEN = 'OPEN'
    ACKNOWLEDGED = 'ACKNOWLEDGED'
    IN_PROGRESS = 'IN_PROGRESS'
    RESOLVED = 'RESOLVED'
    CLOSED = 'CLOSED'

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


class Inspection(Base):
    __tablename__ = 'inspections'
    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey('tasks.id'), nullable=False)
    passed = Column(Boolean, nullable=False)
    notes = Column(Text, nullable=True)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Issue(Base):
    __tablename__ = 'issues'
    id = Column(String, primary_key=True)
    location_id = Column(String, nullable=False)
    unit_id = Column(String, ForeignKey('units.id'), nullable=False)
    category = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(IssueStatus), default=IssueStatus.OPEN)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class TaskStatusEvent(Base):
    __tablename__ = 'task_status_events'
    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey('tasks.id'), nullable=False)
    old_status = Column(String, nullable=False)
    new_status = Column(String, nullable=False)
    changed_by = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class AuditEvent(Base):
    __tablename__ = 'audit_events'
    id = Column(String, primary_key=True)
    location_id = Column(String, nullable=False)
    actor_user_id = Column(String, nullable=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    payload_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
