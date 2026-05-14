import importlib
import sys
import os
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Ensure repository root is on sys.path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import app models and helper to ensure models are registered
from apps.api.app.cli.ensure_business_membership import ensure_business_membership
from apps.api.app.models.user import User
from apps.api.app.models.tenant import Business
from apps.api.app.models.access_control import Membership, Role, ScopedRoleAssignment

# Setup in-memory DB
engine = create_engine("sqlite://", future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

# Ensure models are imported so metadata is populated
importlib.import_module('apps.api.app.models.access_control')
importlib.import_module('apps.api.app.models.tenant')
importlib.import_module('apps.api.app.models.user')
from apps.api.app.models.base import Base
Base.metadata.create_all(engine)

@contextmanager
def db_session():
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except:
        s.rollback()
        raise
    finally:
        s.close()


def test_ensure_business_membership_idempotent():
    with db_session() as db:
        # create user
        u = User(email='relink-test@example.com', hashed_password='')
        db.add(u)
        db.flush()
        # Run ensure
        res1 = ensure_business_membership(db, 'relink-test@example.com', business_name='Relink Biz')
        assert 'business_id' in res1
        assert 'membership_id' in res1
        assert 'owner_role_id' in res1
        # Re-run should not create duplicates and should be idempotent
        res2 = ensure_business_membership(db, 'relink-test@example.com', business_name='Relink Biz')
        assert res2['business_id'] == res1['business_id']
        assert res2['membership_id'] == res1['membership_id']
        assert res2['owner_role_id'] == res1['owner_role_id']

        # Assert DB rows exist
        biz = db.execute(select(Business).where(Business.name == 'Relink Biz')).scalar_one()
        assert biz.name == 'Relink Biz'
        m = db.execute(select(Membership).where(Membership.user_id == u.id, Membership.business_id == biz.id)).scalar_one()
        assert m.user_id == u.id
        role = db.execute(select(Role).where(Role.business_id == biz.id, Role.name == 'Owner')).scalar_one()
        # Scoped assignment exists
        sra = db.execute(select(ScopedRoleAssignment).where(ScopedRoleAssignment.membership_id == m.id, ScopedRoleAssignment.role_id == role.id)).scalar_one_or_none()
        assert sra is not None


def test_missing_user_raises():
    with db_session() as db:
        with pytest.raises(ValueError):
            ensure_business_membership(db, 'no-such-user@example.com', business_name='X')
