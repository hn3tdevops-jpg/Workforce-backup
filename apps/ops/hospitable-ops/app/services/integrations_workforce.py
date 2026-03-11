import httpx
from typing import List
from apps.api.app.db.session import SessionLocal, engine, Base
from apps.api.app.models.integrations_models import EmployeeRef, ShiftRef
import uuid

client = httpx.Client(timeout=10.0)

# Ensure tables exist for skeleton
def init_integration_db():
    Base.metadata.create_all(bind=engine)

def fetch_roster(date, location_id) -> List[dict]:
    # Placeholder: call external Workforce API; return list of employees
    # Real implementation uses httpx async client and authentication
    return []

def fetch_shifts(date, location_id) -> List[dict]:
    return []

def upsert_employee_ref(payload: dict):
    db = SessionLocal()
    try:
        er = EmployeeRef(id=str(uuid.uuid4()), location_id=payload['location_id'], external_employee_id=payload['external_employee_id'], display_name=payload.get('display_name'))
        db.merge(er)
        db.commit()
        return er
    finally:
        db.close()

def upsert_shift_ref(payload: dict):
    db = SessionLocal()
    try:
        sr = ShiftRef(id=str(uuid.uuid4()), location_id=payload['location_id'], external_shift_id=payload['external_shift_id'], external_employee_id=payload.get('external_employee_id'), start_at=payload.get('start_at'), end_at=payload.get('end_at'))
        db.merge(sr)
        db.commit()
        return sr
    finally:
        db.close()
