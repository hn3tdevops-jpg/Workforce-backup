import pytest

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from packages.workforce.workforce.app.models.base import Base
from packages.workforce.workforce.app.models.identity import (
    User, Membership, BizRole, MembershipLocationRole, AuditEvent
)
from packages.workforce.workforce.app.models.business import Business, Location
from packages.workforce.workforce.app.services.tenant_service import set_member_location_roles_service

# Use an isolated in-memory SQLite DB for tests
engine = create_engine("sqlite://", future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

# Ensure models are imported so metadata is populated
import importlib
importlib.import_module('packages.workforce.workforce.app.models')
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


def test_location_owner_can_assign_location_role():
    with db_session() as db:
        owner = User(email='owner@example.com', is_superadmin=False, hashed_password='')
        target = User(email='target@example.com', is_superadmin=False, hashed_password='')
        db.add_all([owner, target])
        db.flush()

        biz = Business(id='biz-assign-1', name='Biz Assign')
        db.add(biz)
        db.flush()

        loc = Location(id='loc-assign-1', business_id=biz.id, name='LocAssign', timezone='UTC')
        db.add(loc)
        db.flush()

        m_owner = Membership(user_id=owner.id, business_id=biz.id, status='active')
        m_target = Membership(user_id=target.id, business_id=biz.id, status='active')
        db.add_all([m_owner, m_target])
        db.flush()

        role_owner = BizRole(id='role-owner-1', name='Location Owner', scope_type='LOCATION', business_id=biz.id)
        role_loc = BizRole(id='role-loc-1', name='Location Role', scope_type='LOCATION', business_id=biz.id)
        db.add_all([role_owner, role_loc])
        db.flush()

        # assign owner as Location Owner at loc
        db.add(MembershipLocationRole(membership_id=m_owner.id, location_id=loc.id, role_id=role_owner.id))
        db.flush()

        assignments = {loc.id: [role_loc.id]}
        job_title_labels = {}
        result = set_member_location_roles_service(biz.id, m_target.id, assignments, job_title_labels, db, owner)

        rows = db.execute(select(MembershipLocationRole).where(MembershipLocationRole.membership_id == m_target.id, MembershipLocationRole.location_id == loc.id)).scalars().all()
        assert any(r.role_id == role_loc.id for r in rows)

        audits = db.execute(select(AuditEvent).where(AuditEvent.entity_id == m_target.id, AuditEvent.action == 'rbac.location_roles.assign')).scalars().all()
        assert len(audits) >= 1


def test_last_location_owner_guard_prevents_removal():
    with db_session() as db:
        u = User(email='solo_owner@example.com', is_superadmin=False, hashed_password='')
        db.add(u); db.flush()
        biz = Business(id='biz-guard-1', name='Biz Guard')
        db.add(biz); db.flush()
        loc = Location(id='loc-guard-1', business_id=biz.id, name='LocGuard', timezone='UTC')
        db.add(loc); db.flush()
        m = Membership(user_id=u.id, business_id=biz.id, status='active')
        db.add(m); db.flush()
        role_owner = BizRole(id='role-owner-guard', name='Location Owner', scope_type='LOCATION', business_id=biz.id)
        db.add(role_owner); db.flush()
        db.add(MembershipLocationRole(membership_id=m.id, location_id=loc.id, role_id=role_owner.id))
        db.flush()

        assignments = {loc.id: []}
        job_title_labels = {}
        with pytest.raises(ValueError):
            set_member_location_roles_service(biz.id, m.id, assignments, job_title_labels, db, u)


def test_superadmin_removal_writes_audit():
    with db_session() as db:
        admin = User(email='admin@example.com', is_superadmin=True, hashed_password='')
        member = User(email='member@example.com', is_superadmin=False, hashed_password='')
        db.add_all([admin, member]); db.flush()
        biz = Business(id='biz-rem-1', name='Biz Rem')
        db.add(biz); db.flush()
        loc = Location(id='loc-rem-1', business_id=biz.id, name='LocRem', timezone='UTC')
        db.add(loc); db.flush()
        m_member = Membership(user_id=member.id, business_id=biz.id, status='active')
        m_admin = Membership(user_id=admin.id, business_id=biz.id, status='active')
        db.add_all([m_member, m_admin]); db.flush()
        role = BizRole(id='role-rem-1', name='Some Location Role', scope_type='LOCATION', business_id=biz.id)
        db.add(role); db.flush()
        db.add(MembershipLocationRole(membership_id=m_member.id, location_id=loc.id, role_id=role.id))
        db.flush()

        assignments = {loc.id: []}
        job_title_labels = {}
        res = set_member_location_roles_service(biz.id, m_member.id, assignments, job_title_labels, db, admin)

        audits = db.execute(select(AuditEvent).where(AuditEvent.entity_id == m_member.id, AuditEvent.action == 'rbac.location_roles.remove')).scalars().all()
        assert len(audits) >= 1


def test_last_location_owner_guard_regression():
    with db_session() as db:
        u = User(email='solo_owner_regression@example.com', is_superadmin=False, hashed_password='')
        db.add(u); db.flush()
        biz = Business(id='biz-guard-2', name='Biz Guard')
        db.add(biz); db.flush()
        loc = Location(id='loc-guard-2', business_id=biz.id, name='LocGuard', timezone='UTC')
        db.add(loc); db.flush()
        m = Membership(user_id=u.id, business_id=biz.id, status='active')
        db.add(m); db.flush()
        role_owner = BizRole(id='role-owner-guard-2', name='Location Owner', scope_type='LOCATION', business_id=biz.id)
        db.add(role_owner); db.flush()
        db.add(MembershipLocationRole(membership_id=m.id, location_id=loc.id, role_id=role_owner.id))
        db.flush()

        assignments = {loc.id: []}
        job_title_labels = {}
        with pytest.raises(ValueError):
            set_member_location_roles_service(biz.id, m.id, assignments, job_title_labels, db, u)