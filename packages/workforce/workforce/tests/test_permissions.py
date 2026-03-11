import os
import pytest
os.environ.setdefault("DATABASE_URL", "sqlite://")
from apps.api.app.core.db import engine, db_session
from apps.api.app.models.base import Base
# Ensure in-memory test DB has schema
Base.metadata.create_all(engine)
from apps.api.app.core.auth_deps import _get_user_permissions
from apps.api.app.models.identity import User, Membership, BizRole, BizRolePermission, Permission, MembershipRole
from apps.api.app.models.business import Business



def test_user_permissions_basic():
    # seed minimal data using db_session context manager
    with db_session() as db:
        u = User(email='perm@example.com', is_superadmin=False, hashed_password='')
        db.add(u)
        db.flush()

        b_id = 'biz-1'
        # create business record referenced by membership FK
        biz = Business(id=b_id, name='Test Biz')
        db.add(biz)
        db.flush()
        m = Membership(user_id=u.id, business_id=b_id, status='active')
        db.add(m)
        db.flush()

        # create role and permission
        p = Permission(key='members:read')
        db.add(p)
        db.flush()
        r = BizRole(id='role-1', name='Role 1')
        db.add(r)
        db.flush()
        rp = BizRolePermission(role_id=r.id, permission_id=p.id)
        db.add(rp)
        db.flush()

        # assign membership role
        mr = MembershipRole(membership_id=m.id, role_id=r.id)
        db.add(mr)
        db.flush()

        perms = _get_user_permissions(u, b_id, db)
        assert 'members:read' in perms
