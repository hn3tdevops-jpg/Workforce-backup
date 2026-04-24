import pytest
from sqlalchemy import select

from app.db.base import Base, import_core_models
from apps.api.app.models.access_control import (
    Membership,
    Permission,
    Role,
    RolePermission,
    ScopedRoleAssignment,
)
from apps.api.app.models.tenant import Business, Location, Tenant
from apps.api.app.models.user import User
from apps.api.app.services.async_rbac import (
    get_effective_role_names_async,
    get_effective_permission_codes_async,
    user_has_permission_async,
)


@pytest.mark.asyncio
async def test_async_rbac_permission_checks(db_session):
    # Prepare in-memory DB via fixtures
    import_core_models()
    # Create all metadata on the underlying sync engine via run_sync
    await db_session.run_sync(lambda session: Base.metadata.create_all(session.get_bind()))

    tenant = Tenant(name="Tenant A", slug="t-a")
    business = Business(name="Biz A", tenant=tenant)
    location_a = Location(name="Loc A", business=business)
    location_b = Location(name="Loc B", business=business)
    user = User(email="async@example.com", hashed_password="x")
    db_session.add_all([tenant, business, location_a, location_b, user])
    await db_session.flush()

    membership = Membership(user_id=user.id, business_id=business.id, status="active")
    db_session.add(membership)
    await db_session.flush()

    role = Role(business_id=business.id, name="Scheduler")
    db_session.add(role)
    await db_session.flush()

    permission = Permission(code="schedule.read", resource="schedule", action="read", description="")
    db_session.add(permission)
    await db_session.flush()

    db_session.add(RolePermission(role_id=role.id, permission_id=permission.id))
    await db_session.flush()

    db_session.add(ScopedRoleAssignment(membership_id=membership.id, role_id=role.id, location_id=None))
    await db_session.commit()

    roles = await get_effective_role_names_async(db_session, user.id, business.id, None)
    assert "Scheduler" in roles

    perms = await get_effective_permission_codes_async(db_session, user.id, business.id, None)
    assert "schedule.read" in perms

    assert await user_has_permission_async(db_session, user.id, "schedule.read", business.id, None)
