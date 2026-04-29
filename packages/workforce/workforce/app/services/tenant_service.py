import json
from datetime import datetime as _dt, timezone as _tz
from typing import Dict, List

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from packages.workforce.workforce.app.core.auth_deps import _get_user_location_permissions
from packages.workforce.workforce.app.models.business import Location
from packages.workforce.workforce.app.models.identity import (
    BizRole, Membership, MembershipLocationRole, MembershipStatus, AuditEvent, User,
)


def set_member_location_roles_service(
    business_id: str,
    membership_id: str,
    assignments: Dict[str, List[str]],
    job_title_labels: Dict[str, Dict[str, str]],
    db: Session,
    actor: User | None = None,
) -> Dict[str, List[str]]:
    """Business logic extracted from the tenant route.

    - assignments: mapping location_id -> list of role_ids
    - job_title_labels: mapping location_id -> { role_id: label }
    - db: SQLAlchemy Session
    - actor: SQLAlchemy User instance for the caller (may be None)

    Returns mapping location_id -> list of role_ids after the change.
    """
    def _is_location_owner(user_id: str, location_id: str) -> bool:
        if not user_id:
            return False
        q = (
            select(MembershipLocationRole, BizRole)
            .join(BizRole, BizRole.id == MembershipLocationRole.role_id)
            .join(Membership, Membership.id == MembershipLocationRole.membership_id)
            .where(
                Membership.user_id == user_id,
                Membership.business_id == business_id,
                MembershipLocationRole.location_id == location_id,
                BizRole.name.ilike('location owner'),
                Membership.status == MembershipStatus.active,
            )
        )
        rows = db.execute(q).all()
        return len(rows) > 0

    def _location_owner_rows(location_id: str, membership_id_to_skip: str | None = None):
        q = (
            select(MembershipLocationRole)
            .join(BizRole, BizRole.id == MembershipLocationRole.role_id)
            .join(Membership, Membership.id == MembershipLocationRole.membership_id)
            .where(
                MembershipLocationRole.location_id == location_id,
                BizRole.name.ilike('location owner'),
                Membership.status == MembershipStatus.active,
            )
        )
        if membership_id_to_skip is not None:
            q = q.where(MembershipLocationRole.membership_id != membership_id_to_skip)
        return db.execute(q).scalars().all()

    for location_id, role_ids in assignments.items():
        loc = db.execute(
            select(Location).where(Location.id == location_id, Location.business_id == business_id)
        ).scalar_one_or_none()
        if not loc:
            raise ValueError(f"Location {location_id} not found in this business")

        location_scoped_roles = []
        for role_id in role_ids:
            role = db.execute(
                select(BizRole).where(BizRole.id == role_id, BizRole.business_id == business_id)
            ).scalar_one_or_none()
            if not role:
                raise ValueError(f"Role {role_id} not found in this business")
            if role.scope_type == 'LOCATION':
                location_scoped_roles.append(role)

        existing_rows = db.execute(
            select(MembershipLocationRole, BizRole)
            .join(BizRole, BizRole.id == MembershipLocationRole.role_id)
            .where(
                MembershipLocationRole.membership_id == membership_id,
                MembershipLocationRole.location_id == location_id,
            )
        ).all()

        existing_owner_removal_guard = False
        for mlr, role in existing_rows:
            if role.scope_type == 'LOCATION' and role.name.lower() == 'location owner' and role.id not in role_ids:
                existing_owner_removal_guard = True

        if location_scoped_roles or existing_owner_removal_guard:
            if actor and getattr(actor, 'is_superadmin', False):
                caller_allowed = True
            else:
                caller_perms = _get_user_location_permissions(actor, business_id, location_id, db) if actor else set()
                caller_allowed = ('*' in caller_perms) or ('rbac.location_roles.manage' in caller_perms) or ('rbac.location_assignments.manage' in caller_perms)
                if not caller_allowed and actor:
                    caller_allowed = _is_location_owner(actor.id, location_id)
            if not caller_allowed:
                raise PermissionError("Location-owner delegation required: missing rbac.location_roles.manage or location owner role")

        removed_rows = db.execute(
            select(MembershipLocationRole).where(
                MembershipLocationRole.membership_id == membership_id,
                MembershipLocationRole.location_id == location_id,
            )
        ).scalars().all()
        removed_role_ids = [r.role_id for r in removed_rows]

        if existing_owner_removal_guard:
            others = _location_owner_rows(location_id, membership_id_to_skip=membership_id)
            if not others:
                raise ValueError("Cannot remove last Location Owner for this location")

        db.execute(
            delete(MembershipLocationRole).where(
                MembershipLocationRole.membership_id == membership_id,
                MembershipLocationRole.location_id == location_id,
            )
        )

        if removed_role_ids:
            audit = AuditEvent(
                business_id=business_id,
                actor_type='user',
                actor_id=actor.id if actor else None,
                action='rbac.location_roles.remove',
                entity='membership_location_role',
                entity_id=membership_id,
                diff_json=json.dumps({'location_id': location_id, 'removed_role_ids': removed_role_ids}),
                created_at=_dt.now(_tz.utc),
            )
            db.add(audit)

        loc_labels = job_title_labels.get(location_id, {}) if job_title_labels else {}
        for role_id in role_ids:
            db.add(MembershipLocationRole(
                membership_id=membership_id,
                location_id=location_id,
                role_id=role_id,
                job_title_label=loc_labels.get(role_id),
                created_by_user_id=actor.id if actor else None,
            ))

        if role_ids:
            audit = AuditEvent(
                business_id=business_id,
                actor_type='user',
                actor_id=actor.id if actor else None,
                action='rbac.location_roles.assign',
                entity='membership_location_role',
                entity_id=membership_id,
                diff_json=json.dumps({'location_id': location_id, 'assigned_role_ids': role_ids}),
                created_at=_dt.now(_tz.utc),
            )
            db.add(audit)

    db.commit()

    rows = db.execute(
        select(MembershipLocationRole).where(MembershipLocationRole.membership_id == membership_id)
    ).scalars().all()
    result: Dict[str, List[str]] = {}
    for r in rows:
        result.setdefault(r.location_id, []).append(r.role_id)
    return result
