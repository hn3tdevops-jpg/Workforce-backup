"""Permission check helpers used by FastAPI dependencies and services.
Minimal implementation: _require_perm(user_id, business_id, perm_key, db) raises PermissionError if not allowed.
"""
from typing import Optional
import sqlalchemy as sa

class PermissionDenied(Exception):
    pass


def _user_permissions(user_id: str, business_id: Optional[str], db):
    """Return set of permission keys for a user within a business (includes business-scoped roles and location-scoped roles across locations).
    """
    # Query role assignments joined to role_permissions -> permissions
    sql = sa.text("""
    SELECT p.key FROM user_role_assignments ura
    JOIN role_permissions rp ON rp.role_id = ura.role_id
    JOIN permissions p ON p.id = rp.permission_id
    WHERE ura.user_id = :user_id
      AND ura.business_id = :business_id
    """)
    rows = db.execute(sql, {'user_id': user_id, 'business_id': business_id}).fetchall()
    return {r[0] for r in rows}


def require_perm(user_id: str, business_id: str, perm_key: str, db):
    perms = _user_permissions(user_id, business_id, db)
    if perm_key not in perms:
        raise PermissionDenied(f"User {user_id} lacks permission {perm_key} for business {business_id}")
