from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.dependencies import AuthContext, get_current_auth_context, require_permission
from apps.api.app.db.session import get_async_session
from apps.api.app.models.user_employee_link import UserEmployeeLink
from apps.api.app.schemas.employee import EmployeeCreate, EmployeeRead, UserEmployeeLinkCreate, UserEmployeeLinkRead
from apps.api.app.services.employee_service import create_employee, link_user_to_employee
from apps.api.app.services.rbac_service import user_has_permission

router = APIRouter()


@router.post("/", response_model=EmployeeRead, status_code=201)
async def post_employee(
    payload: EmployeeCreate,
    session: AsyncSession = Depends(get_async_session),
    _auth: AuthContext = Depends(require_permission("users.manage")),
):
    emp = await create_employee(session, payload)
    return EmployeeRead(
        id=emp.id,
        business_id=emp.business_id,
        location_id=emp.location_id,
        first_name=emp.first_name,
        last_name=emp.last_name,
        email_work=emp.email_work,
        is_active=emp.is_active,
    )


@router.post("/link-user/{user_id}", response_model=UserEmployeeLinkRead, status_code=201)
async def post_link_user(
    user_id: uuid.UUID,
    payload: UserEmployeeLinkCreate,
    session: AsyncSession = Depends(get_async_session),
    auth: AuthContext = Depends(get_current_auth_context),
):
    existing = await session.scalar(
        select(UserEmployeeLink).where(
            (UserEmployeeLink.user_id == user_id) | (UserEmployeeLink.employee_id == payload.employee_id),
            UserEmployeeLink.is_active.is_(True),
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User or Employee already linked")

    allowed = await session.run_sync(
        lambda sync_session: user_has_permission(
            sync_session,
            auth.user_id,
            "users.manage",
            auth.business_id,
            None,
        )
    )
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions.")

    link = await link_user_to_employee(session, auth, user_id, payload.employee_id)
    return UserEmployeeLinkRead(
        id=link.id,
        user_id=link.user_id,
        employee_id=link.employee_id,
        business_id=link.business_id,
        is_active=link.is_active,
        created_at=str(link.created_at) if link.created_at is not None else None,
    )
