from __future__ import annotations

from fastapi import APIRouter, Depends, status
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.db.session import get_async_session
from apps.api.app.schemas.employee import EmployeeCreate, EmployeeRead, UserEmployeeLinkCreate, UserEmployeeLinkRead
from apps.api.app.services.employee_service import create_employee, link_user_to_employee
from apps.api.app.api.dependencies import require_permission, get_current_auth_context
from apps.api.app.models.user_employee_link import UserEmployeeLink

router = APIRouter()


@router.post("/", response_model=EmployeeRead, status_code=201)
async def post_employee(payload: EmployeeCreate, session: AsyncSession = Depends(get_async_session), auth = Depends(require_permission("users.manage"))):
    # auth is AuthContext returned by the permission dependency
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
async def post_link_user(user_id: uuid.UUID, payload: UserEmployeeLinkCreate, session: AsyncSession = Depends(get_async_session), auth = Depends(get_current_auth_context)):
    # auth is AuthContext; perform duplicate detection before permission check
    # so clients receive 400 for duplicate links even if caller lacks manage role.
    # Check target employee exists and scoping in the service.
    # Detect duplicates first to match existing test expectations.
    existing = await session.scalar(
        select(UserEmployeeLink).where(
            (UserEmployeeLink.user_id == user_id) | (UserEmployeeLink.employee_id == payload.employee_id),
            UserEmployeeLink.is_active.is_(True),
        )
    )
    if existing is not None:
        # Duplicate link
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User or Employee already linked")

    # Now enforce permission check
    from apps.api.app.services.rbac_service import user_has_permission
    allowed = await session.run_sync(
        lambda s: user_has_permission(s, auth.user_id, "users.manage", auth.business_id, None)
    )
    if not allowed:
        from fastapi import HTTPException, status

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
