import uuid
from app.db.session import SessionLocal, engine, Base
from app.models.rbac_models import Role, Permission, UserRoleAssignment, role_permissions

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
        assignment = UserRoleAssignment(id=str(uuid.uuid4()), user_id=user_id, business_id=business_id, scope_type=scope_type, location_id=location_id, role_id=role_id, job_title_label=job_title_label, created_by_user_id=created_by_user_id)
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment
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
