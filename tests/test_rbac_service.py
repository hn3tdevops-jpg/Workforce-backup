from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.base import Base, import_core_models
from app.models.access_control import (
    Membership,
    Permission,
    Role,
    RolePermission,
    ScopedRoleAssignment,
)
from app.models.tenant import Business, Location, Tenant
from app.models.user import User
from app.services.rbac_service import (
    get_active_memberships_for_user,
    get_effective_permission_codes,
    get_effective_role_names,
    user_has_permission,
)


def make_session() -> Session:
    import_core_models()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def seed_base(session: Session):
    tenant = Tenant(name="Tenant 1", slug="tenant-1")
    business = Business(name="Business 1", tenant=tenant)
    location_a = Location(name="Location A", business=business)
    location_b = Location(name="Location B", business=business)
    user = User(email="user@example.com", hashed_password="not-real")
    session.add_all([tenant, business, location_a, location_b, user])
    session.flush()
    return tenant, business, location_a, location_b, user


def seed_membership(session: Session, user: User, business: Business, *, is_owner: bool = False) -> Membership:
    membership = Membership(user_id=user.id, business_id=business.id, status="active", is_owner=is_owner)
    session.add(membership)
    session.flush()
    return membership


def seed_role(session: Session, business: Business, name: str) -> Role:
    role = Role(business_id=business.id, name=name)
    session.add(role)
    session.flush()
    return role


def seed_permission(session: Session, code: str) -> Permission:
    resource, action = code.rsplit(".", 1)
    permission = Permission(code=code, resource=resource, action=action, description=code)
    session.add(permission)
    session.flush()
    return permission


def link_role_permission(session: Session, role: Role, permission: Permission) -> None:
    session.add(RolePermission(role_id=role.id, permission_id=permission.id))
    session.flush()


def assign_role(
    session: Session,
    membership: Membership,
    role: Role,
    *,
    location_id=None,
) -> ScopedRoleAssignment:
    assignment = ScopedRoleAssignment(
        membership_id=membership.id,
        role_id=role.id,
        location_id=location_id,
    )
    session.add(assignment)
    session.flush()
    return assignment


def test_business_wide_role_applies_at_business_and_location_scope() -> None:
    session = make_session()
    _, business, location_a, location_b, user = seed_base(session)
    membership = seed_membership(session, user, business)

    role = seed_role(session, business, "Manager")
    permission = seed_permission(session, "schedule.manage")
    link_role_permission(session, role, permission)
    assign_role(session, membership, role, location_id=None)

    session.commit()

    assert "Manager" in get_effective_role_names(session, user.id, business.id, None)
    assert "Manager" in get_effective_role_names(session, user.id, business.id, location_a.id)

    assert user_has_permission(session, user.id, "schedule.manage", business.id, None) is True
    assert user_has_permission(session, user.id, "schedule.manage", business.id, location_a.id) is True
    assert user_has_permission(session, user.id, "schedule.manage", business.id, location_b.id) is True


def test_location_scoped_role_only_applies_at_that_location() -> None:
    session = make_session()
    _, business, location_a, location_b, user = seed_base(session)
    membership = seed_membership(session, user, business)

    role = seed_role(session, business, "Housekeeping Lead")
    permission = seed_permission(session, "hk.tasks.manage")
    link_role_permission(session, role, permission)
    assign_role(session, membership, role, location_id=location_a.id)

    session.commit()

    assert user_has_permission(session, user.id, "hk.tasks.manage", business.id, None) is False
    assert user_has_permission(session, user.id, "hk.tasks.manage", business.id, location_a.id) is True
    assert user_has_permission(session, user.id, "hk.tasks.manage", business.id, location_b.id) is False


def test_effective_permissions_are_union_of_business_and_location_assignments() -> None:
    session = make_session()
    _, business, location_a, location_b, user = seed_base(session)
    membership = seed_membership(session, user, business)

    business_role = seed_role(session, business, "Scheduler")
    business_perm = seed_permission(session, "schedule.read")
    link_role_permission(session, business_role, business_perm)
    assign_role(session, membership, business_role, location_id=None)

    location_role = seed_role(session, business, "Room Ops")
    location_perm = seed_permission(session, "hk.rooms.read")
    link_role_permission(session, location_role, location_perm)
    assign_role(session, membership, location_role, location_id=location_a.id)

    session.commit()

    business_scope = get_effective_permission_codes(session, user.id, business.id, None)
    location_a_scope = get_effective_permission_codes(session, user.id, business.id, location_a.id)
    location_b_scope = get_effective_permission_codes(session, user.id, business.id, location_b.id)

    assert business_scope == {"schedule.read"}
    assert location_a_scope == {"schedule.read", "hk.rooms.read"}
    assert location_b_scope == {"schedule.read"}


def test_only_active_memberships_are_returned() -> None:
    session = make_session()
    tenant, business, _, _, user = seed_base(session)

    other_business = Business(name="Business 2", tenant=tenant)
    session.add(other_business)
    session.flush()

    active = Membership(user_id=user.id, business_id=business.id, status="active", is_owner=False)
    inactive = Membership(user_id=user.id, business_id=other_business.id, status="inactive", is_owner=False)

    session.add_all([active, inactive])
    session.commit()

    memberships = get_active_memberships_for_user(session, user.id)
    assert len(memberships) == 1
    assert memberships[0].status == "active"
    assert memberships[0].business_id == business.id