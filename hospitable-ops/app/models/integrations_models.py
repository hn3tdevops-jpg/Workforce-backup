from sqlalchemy import Column, String, DateTime
from app.db.session import Base

class EmployeeRef(Base):
    __tablename__ = "employee_refs"
    id = Column(String, primary_key=True)
    location_id = Column(String, nullable=False)
    external_employee_id = Column(String, nullable=False)
    display_name = Column(String, nullable=True)

class ShiftRef(Base):
    __tablename__ = "shift_refs"
    id = Column(String, primary_key=True)
    location_id = Column(String, nullable=False)
    external_shift_id = Column(String, nullable=False)
    external_employee_id = Column(String, nullable=True)
    start_at = Column(DateTime, nullable=True)
    end_at = Column(DateTime, nullable=True)
