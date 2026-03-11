from apps.api.app.db.session import SessionLocal, engine, Base
from apps.api.app.models.idempotency_models import IdempotencyKey
import uuid
import hashlib
import json

# Ensure table exists for skeleton
def init_idempotency_db():
    Base.metadata.create_all(bind=engine)


def compute_request_hash(body, path, method):
    h = hashlib.sha256()
    h.update((method + path + json.dumps(body or {}, sort_keys=True)).encode())
    return h.hexdigest()


def get_by_key(key):
    db = SessionLocal()
    try:
        return db.query(IdempotencyKey).filter_by(key=key).first()
    finally:
        db.close()


def create_key_if_missing(key, location_id=None, request_hash=None):
    db = SessionLocal()
    try:
        ik = db.query(IdempotencyKey).filter_by(key=key).first()
        if not ik:
            ik = IdempotencyKey(id=str(uuid.uuid4()), key=key, location_id=location_id, request_hash=request_hash)
            db.add(ik)
            db.commit()
            db.refresh(ik)
        return ik
    finally:
        db.close()


def store_response(key, status, body):
    db = SessionLocal()
    try:
        ik = db.query(IdempotencyKey).filter_by(key=key).first()
        if not ik:
            ik = IdempotencyKey(id=str(uuid.uuid4()), key=key)
        ik.response_status = int(status)
        ik.response_body_json = body
        db.merge(ik)
        db.commit()
        db.refresh(ik)
        return ik
    finally:
        db.close()
