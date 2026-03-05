import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def log_change(
    session: Session,
    actor_type: str,
    actor_id: str | None,
    entity_type: str,
    entity_id: str,
    action: str,
    before_dict: dict[str, Any] | None,
    after_dict: dict[str, Any] | None,
) -> AuditLog:
    entry = AuditLog(
        actor_type=actor_type,
        actor_id=actor_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_json=json.dumps(before_dict, default=str) if before_dict is not None else None,
        after_json=json.dumps(after_dict, default=str) if after_dict is not None else None,
    )
    session.add(entry)
    return entry
