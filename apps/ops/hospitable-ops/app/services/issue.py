import uuid
import json
import datetime
from apps.api.app.db.session import SessionLocal
from apps.api.app.models.housekeeping_models import Issue, IssueStatus, AuditEvent

ALLOWED_TRANSITIONS = {
    IssueStatus.OPEN: [IssueStatus.ACKNOWLEDGED, IssueStatus.IN_PROGRESS, IssueStatus.CLOSED],
    IssueStatus.ACKNOWLEDGED: [IssueStatus.IN_PROGRESS, IssueStatus.CLOSED],
    IssueStatus.IN_PROGRESS: [IssueStatus.RESOLVED, IssueStatus.CLOSED],
    IssueStatus.RESOLVED: [IssueStatus.CLOSED],
}


def create_issue(location_id: str, unit_id: str, category: str = None, severity: str = None,
                 description: str = None, created_by: str = None):
    db = SessionLocal()
    try:
        issue = Issue(
            id=str(uuid.uuid4()),
            location_id=location_id,
            unit_id=unit_id,
            category=category,
            severity=severity,
            description=description,
            created_by=created_by,
        )
        db.add(issue)

        audit = AuditEvent(
            id=str(uuid.uuid4()),
            location_id=location_id,
            actor_user_id=created_by,
            entity_type='issue',
            entity_id=issue.id,
            action='created',
            payload_json=json.dumps({'category': category, 'severity': severity}),
        )
        db.add(audit)
        db.commit()
        db.refresh(issue)
        return issue, None
    finally:
        db.close()


def transition_issue(issue_id: str, new_status: IssueStatus, actor_user_id: str = None):
    db = SessionLocal()
    try:
        issue = db.get(Issue, issue_id)
        if not issue:
            return None, 'issue_not_found'
        if issue.status not in ALLOWED_TRANSITIONS or new_status not in ALLOWED_TRANSITIONS[issue.status]:
            return None, 'invalid_transition'

        old_status = issue.status
        issue.status = new_status
        issue.updated_at = datetime.datetime.utcnow()
        db.add(issue)

        audit = AuditEvent(
            id=str(uuid.uuid4()),
            location_id=issue.location_id,
            actor_user_id=actor_user_id,
            entity_type='issue',
            entity_id=issue_id,
            action='status_transition',
            payload_json=json.dumps({'old': old_status.value, 'new': new_status.value}),
        )
        db.add(audit)
        db.commit()
        db.refresh(issue)
        return issue, None
    finally:
        db.close()
