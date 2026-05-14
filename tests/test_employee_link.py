import pytest

from apps.api.app.core.security import create_access_token
from apps.api.app.db.base import import_models
from apps.api.app.models.access_control import (Membership, Permission, Role,
                                                RolePermission,
                                                ScopedRoleAssignment)
from apps.api.app.models.employee import EmployeeProfile
from apps.api.app.models.tenant import Business
from apps.api.app.models.user import User
from apps.api.app.models.user_employee_link import UserEmployeeLink


@pytest.mark.asyncio
async def test_link_user_to_employee_happy_path(client, db_session):
    # create supporting models
    await db_session.run_sync(import_models)

    business = Business(name="Biz 1")
    await db_session.run_sync(lambda s: s.add(business))
    await db_session.commit()

    # create an actor user (caller) and give them users.manage permission via role
    actor = User(email="actor@example.com", hashed_password="x")
    await db_session.run_sync(lambda s: s.add(actor))
    await db_session.commit()

    # create membership and role+permission
    perm = Permission(code="users.manage", resource="users", action="manage")
    role = Role(business_id=business.id, name="Admin")
    await db_session.run_sync(lambda s: s.add_all([perm, role]))
    await db_session.commit()

    # link role_permission and membership and scoped assignment
    await db_session.run_sync(
        lambda s: s.add(
            Membership(
                user_id=actor.id, business_id=business.id, status="active"
            )
        )
    )
    await db_session.run_sync(
        lambda s: s.add(RolePermission(role_id=role.id, permission_id=perm.id))
    )
    # find membership id
    mem = await db_session.run_sync(
        lambda s: s.scalar(s.query(Membership).filter_by(user_id=actor.id))
    )
    await db_session.run_sync(
        lambda s: s.add(
            ScopedRoleAssignment(membership_id=mem.id, role_id=role.id)
        )
    )
    await db_session.commit()

    # create target user and employee in same business
    target = User(email="target@example.com", hashed_password="x")
    await db_session.run_sync(lambda s: s.add(target))
    emp = EmployeeProfile(
        business_id=business.id, first_name="Jane", last_name="Doe"
    )
    await db_session.run_sync(lambda s: s.add(emp))
    await db_session.commit()

    token = create_access_token(
        user_id=str(actor.id), business_id=str(business.id)
    )

    resp = await client.post(
        f"/api/v1/employees/link-user/{target.id}",
        json={"employee_id": str(emp.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["user_id"] == str(target.id)
    assert data["employee_id"] == str(emp.id)


@pytest.mark.asyncio
async def test_duplicate_link_rejected(client, db_session):
    # setup minimal: create business, actor, target, emp, and existing link
    await db_session.run_sync(import_models)
    business = Business(name="Biz 2")
    await db_session.run_sync(lambda s: s.add(business))
    await db_session.commit()

    actor = User(email="actor2@example.com", hashed_password="x")
    target = User(email="target2@example.com", hashed_password="x")
    emp = EmployeeProfile(
        business_id=business.id, first_name="John", last_name="Smith"
    )
    await db_session.run_sync(lambda s: s.add_all([actor, target, emp]))
    await db_session.commit()

    # create existing link
    link = UserEmployeeLink(
        user_id=target.id, employee_id=emp.id, business_id=business.id
    )
    await db_session.run_sync(lambda s: s.add(link))
    await db_session.commit()

    token = create_access_token(
        user_id=str(actor.id), business_id=str(business.id)
    )

    resp = await client.post(
        f"/api/v1/employees/link-user/{target.id}",
        json={"employee_id": str(emp.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_cross_business_link_rejected(client, db_session):
    await db_session.run_sync(import_models)
    biz_a = Business(name="A")
    biz_b = Business(name="B")
    await db_session.run_sync(lambda s: s.add_all([biz_a, biz_b]))
    await db_session.commit()

    actor = User(email="actor3@example.com", hashed_password="x")
    target = User(email="target3@example.com", hashed_password="x")
    emp = EmployeeProfile(business_id=biz_b.id, first_name="X", last_name="Y")
    await db_session.run_sync(lambda s: s.add_all([actor, target, emp]))
    await db_session.commit()

    # actor's token claims business A but employee is in business B
    token = create_access_token(
        user_id=str(actor.id), business_id=str(biz_a.id)
    )

    resp = await client.post(
        f"/api/v1/employees/link-user/{target.id}",
        json={"employee_id": str(emp.id)},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
