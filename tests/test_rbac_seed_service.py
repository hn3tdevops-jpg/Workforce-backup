from __future__ import annotations

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.db.base import Base, import_core_models
from app.models.access_control import Permission, Role, RolePermission
from app.models.tenant import Business, Tenant
from app.services.rbac_seed_service import (DEFAULT_ROLE_PERMISSION_CODES,
                                            seed_default_roles_for_business)


def make_session() -> Session:
    import_core_models()
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def seed_business(session: Session) -> Business:
    tenant = Tenant(name="Tenant 1", slug="tenant-1")
    business = Business(name="Business 1", tenant=tenant)
    session.add_all([tenant, business])
    session.flush()
    return business


def role_permission_codes(session: Session, role: Role) -> set[str]:
    stmt = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role.id)
    )
    return set(session.scalars(stmt).all())


def test_seed_default_roles_creates_expected_roles() -> None:
    session = make_session()
    business = seed_business(session)

    roles = seed_default_roles_for_business(session, business.id)
    session.commit()

    assert set(roles.keys()) == set(DEFAULT_ROLE_PERMISSION_CODES.keys())

    db_roles = session.scalars(
        select(Role).where(Role.business_id == business.id)
    ).all()
    assert {role.name for role in db_roles} == set(
        DEFAULT_ROLE_PERMISSION_CODES.keys()
    )


def test_seed_default_roles_assigns_expected_permissions() -> None:
    session = make_session()
    business = seed_business(session)

    roles = seed_default_roles_for_business(session, business.id)
    session.commit()

    for role_name, expected_codes in DEFAULT_ROLE_PERMISSION_CODES.items():
        actual_codes = role_permission_codes(session, roles[role_name])
        assert actual_codes == expected_codes


def test_seed_default_roles_is_idempotent() -> None:
    session = make_session()
    business = seed_business(session)

    seed_default_roles_for_business(session, business.id)
    seed_default_roles_for_business(session, business.id)
    session.commit()

    role_count = session.scalar(
        select(func.count())
        .select_from(Role)
        .where(Role.business_id == business.id)
    )
    permission_count = session.scalar(
        select(func.count()).select_from(Permission)
    )
    role_permission_count = session.scalar(
        select(func.count()).select_from(RolePermission)
    )

    assert role_count == len(DEFAULT_ROLE_PERMISSION_CODES)
    assert permission_count == len(
        set().union(*DEFAULT_ROLE_PERMISSION_CODES.values())
    )
    assert role_permission_count == sum(
        len(v) for v in DEFAULT_ROLE_PERMISSION_CODES.values()
    )
