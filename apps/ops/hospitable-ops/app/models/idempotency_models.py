from sqlalchemy import Column, String, DateTime, Integer, JSON
from apps.api.app.db.session import Base
import datetime

class IdempotencyKey(Base):
    __tablename__ = 'idempotency_keys'
    id = Column(String, primary_key=True)
    location_id = Column(String, nullable=True)
    key = Column(String, nullable=False, unique=True)
    request_hash = Column(String, nullable=True)
    response_status = Column(Integer, nullable=True)
    response_body_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
