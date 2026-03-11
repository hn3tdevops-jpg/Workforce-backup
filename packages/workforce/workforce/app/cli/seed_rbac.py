"""Seed initial RBAC roles and permissions.
This script is minimal: it uses the project's DB session helpers to insert core permissions and a baseline admin role.
Run with: python -m app.cli.seed_rbac
"""

from apps.api.app.core.db import db_session
from datetime import datetime
import sqlalchemy as sa

# fallback imports if packages are modules
try:
    from apps.api.app.models.roles import Role
    from apps.api.app.models.permissions import Permission
except Exception:
    # models may already be imported elsewhere; keep minimal to avoid import errors in test env
    Role = None
    Permission = None

PERMISSIONS = [
    'employees.read',
    'employees.write',
    'rbac.location_roles.manage',
    'rbac.location_assignments.manage',
]

def seed():
    with db_session() as db:
        # Insert permissions if missing
        for key in PERMISSIONS:
            db.execute(
                sa.text("INSERT OR IGNORE INTO permissions (key) VALUES (:key)"),
                {'key': key}
            )
        # Insert a baseline admin role
        db.execute(
            sa.text("INSERT OR IGNORE INTO roles (id, name) VALUES (:id, :n)"),
            {'id': 'platform-admin', 'n': 'Platform Admin'}
        )

if __name__ == '__main__':
    seed()
    print('Seeded RBAC permissions (idempotent)')
