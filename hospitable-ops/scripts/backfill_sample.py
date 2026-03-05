"""Sample idempotent backfill: populate missing employee refs from a CSV"""
import csv
from app.db.session import SessionLocal, engine, Base
from app.models.integrations_models import EmployeeRef
import uuid

def backfill_from_csv(path):
    db = SessionLocal()
    try:
        with open(path) as f:
            r = csv.DictReader(f)
            for row in r:
                existing = db.query(EmployeeRef).filter_by(location_id=row['location_id'], external_employee_id=row['external_employee_id']).first()
                if existing:
                    continue
                er = EmployeeRef(id=str(uuid.uuid4()), location_id=row['location_id'], external_employee_id=row['external_employee_id'], display_name=row.get('display_name'))
                db.add(er)
            db.commit()
    finally:
        db.close()

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('usage: backfill_sample.py data.csv')
    else:
        backfill_from_csv(sys.argv[1])
