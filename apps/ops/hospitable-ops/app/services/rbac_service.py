import uuid
import logging
from apps.api.app.db.session import SessionLocal, engine, Base
from apps.api.app.models.rbac_models import Role, Permission, UserRoleAssignment, role_permissions
from apps.api.app.services.audit import log_change

# Ensure tables exist for the skeleton
def init_db():
    Base.metadata.create_all(bind=engine)

def create_role(business_id: str, scope_type: str, name: str, location_id: str = None, priority: int = 0):
    db = SessionLocal()
    try:
        role = Role(id=str(uuid.uuid4()), business_id=business_id, scope_type=scope_type, location_id=location_id, name=name, priority=priority)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    finally:
        db.close()

def create_permission(key: str):
    db = SessionLocal()
    try:
        existing = db.query(Permission).filter_by(key=key).first()
        if existing:
            return existing
        perm = Permission(id=str(uuid.uuid4()), key=key)
        db.add(perm)
        db.commit()
        db.refresh(perm)
        return perm
    finally:
        db.close()

def add_permission_to_role(role_id: str, permission_key: str):
    db = SessionLocal()
    try:
        role = db.get(Role, role_id)
        perm = db.query(Permission).filter_by(key=permission_key).first()
        if not perm:
            perm = create_permission(permission_key)
        role.permissions.append(perm)
        db.add(role)
        db.commit()
        return True
    finally:
        db.close()

def assign_role_to_user(user_id: str, business_id: str, scope_type: str, role_id: str, location_id: str = None, job_title_label: str = None, created_by_user_id: str = None):
    db = SessionLocal()
    try:
        # Validate role scope matches provided scope and location presence
        role = db.get(Role, role_id)
        if not role:
            raise ValueError(f"Role not found: {role_id}")
        if role.scope_type == 'LOCATION' and not location_id:
            raise ValueError("location_id is required for LOCATION-scoped role")
        if role.scope_type == 'BUSINESS' and location_id:
            raise ValueError("location_id must be None for BUSINESS-scoped role")

        assignment = UserRoleAssignment(id=str(uuid.uuid4()), user_id=user_id, business_id=business_id, scope_type=scope_type, location_id=location_id, role_id=role_id, job_title_label=job_title_label, created_by_user_id=created_by_user_id)
        db.add(assignment)
        # Audit log the assignment creation
        try:
            after = {"user_id": user_id, "business_id": business_id, "role_id": role_id, "scope_type": scope_type, "location_id": location_id}
            log_change(db, actor_type='user', actor_id=created_by_user_id, entity_type='user_role_assignments', entity_id=assignment.id, action='create_assignment', before_dict=None, after_dict=after)
        except Exception:
            logging.exception("Failed to write audit log for role assignment")
        db.commit()
        db.refresh(assignment)
        return assignment
    finally:
        db.close()


def remove_assignment(assignment_id: str, acting_user_id: str = None) -> bool:
    """Remove a user_role_assignment with guard to prevent deleting the last Location Owner for a location.

    Returns True if deleted, raises ValueError on guard violation, or False if not found.
    """
    db = SessionLocal()
    try:
        assignment = db.get(UserRoleAssignment, assignment_id)
        if not assignment:
            return False
        role = db.get(Role, assignment.role_id)
        # Determine if this is a sensitive role (Location Owner) by name or permissions
        is_location_owner_role = (role.scope_type == 'LOCATION' and role.name.lower() == 'location owner')
        perm_keys = {p.key for p in role.permissions}
        has_owner_perm = 'rbac.location_roles.manage' in perm_keys or 'rbac.location_assignments.manage' in perm_keys
        if role.scope_type == 'LOCATION' and (is_location_owner_role or has_owner_perm):
            count = db.query(UserRoleAssignment).filter_by(business_id=assignment.business_id, role_id=role.id, location_id=assignment.location_id).count()
            if count <= 1:
                raise ValueError("Cannot remove last Location Owner for this location")
        # Audit log before deletion
        try:
            before = {"user_id": assignment.user_id, "business_id": assignment.business_id, "role_id": assignment.role_id, "location_id": assignment.location_id}
            log_change(db, actor_type='user', actor_id=acting_user_id, entity_type='user_role_assignments', entity_id=assignment.id, action='delete_assignment', before_dict=before, after_dict=None)
        except Exception:
            logging.exception("Failed to write audit log for role removal")
        db.delete(assignment)
        db.commit()
        return True
    finally:
        db.close()

def get_user_permissions(user_id: str, location_id: str = None):
    db = SessionLocal()
    try:
        # business-scoped and location-scoped assignments
        assignments = db.query(UserRoleAssignment).filter_by(user_id=user_id).all()
        perms = set()
        for a in assignments:
            role = db.get(Role, a.role_id)
            for p in role.permissions:
                perms.add(p.key)
        return list(perms)
    finally:
        db.close()
