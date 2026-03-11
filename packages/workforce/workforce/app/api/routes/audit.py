from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from apps.api.app.api.deps import get_session
from apps.api.app.models.audit import AuditLog

router = APIRouter(tags=["audit"])


@router.get("/audit")
def list_audit(
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_session),
):
    stmt = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [
        {
            "id": r.id,
            "actor_type": r.actor_type,
            "actor_id": r.actor_id,
            "entity_type": r.entity_type,
            "entity_id": r.entity_id,
            "action": r.action,
            "created_at": r.created_at,
        }
        for r in rows
    ]
