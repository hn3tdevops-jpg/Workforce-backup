import uuid
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.db.base import Base, import_models
from apps.api.app.core.security import hash_password
from apps.api.app.models.user import User
from apps.api.app.cli.ensure_business_membership import ensure_business_membership

# Use in-memory SQLite for this test

def setup_in_memory_db():
    engine = create_engine('sqlite:///:memory:', future=True)
    import_models()
    Base.metadata.create_all(bind=engine)
    return engine


def test_ensure_membership_and_login_flow():
    engine = setup_in_memory_db()
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)
    session = SessionLocal()
    try:
        # create a user
        user = User(id=uuid.uuid4(), email='test@example.com', hashed_password=hash_password('Passw0rd!'), is_active=True)
        session.add(user)
        session.commit()

        # ensure business membership for user email
        res = ensure_business_membership(session, user_email='test@example.com', business_name='TestBiz')
        assert res is not None

        # re-run ensure to confirm idempotency
        res2 = ensure_business_membership(session, user_email='test@example.com', business_name='TestBiz')
        assert res2['business_id'] == res['business_id']

        # check user memberships exist
        from apps.api.app.services.rbac_service import get_active_memberships_for_user
        memberships = get_active_memberships_for_user(session=session, user_id=user.id)
        assert len(memberships) >= 1
    finally:
        session.close()
