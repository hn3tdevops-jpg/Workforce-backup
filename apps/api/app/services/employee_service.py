from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models.employee import EmployeeProfile
from apps.api.app.models.user import User
from apps.api.app.models.user_employee_link import UserEmployeeLink
from apps.api.app.api.dependencies import AuthContext


async def create_employee(session: AsyncSession, payload) -> EmployeeProfile:
    # minimal creation, assume payload is EmployeeCreate pydantic model
    emp = EmployeeProfile(
        business_id=payload.business_id,
        location_id=payload.location_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        external_id=payload.external_id,
        email_work=str(payload.email_work) if payload.email_work else None,
    )
    session.add(emp)
    await session.commit()
    await session.refresh(emp)
    return emp


async def link_user_to_employee(
    session: AsyncSession,
    actor: AuthContext,
    user_id: uuid.UUID,
    employee_id: uuid.UUID,
) -> UserEmployeeLink:
    # Ensure employee exists
    employee = await session.scalar(select(EmployeeProfile).where(EmployeeProfile.id == employee_id))
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Enforce business scoping: actor.business_id must match employee.business_id
    if str(actor.business_id) != str(employee.business_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cross-business linking is not allowed")

    # Ensure user exists
    user = await session.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # If user has an assigned business, it must match employee's business
    if user.business_id is not None and str(user.business_id) != str(employee.business_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User belongs to different business")

    # Check duplicates: user or employee already linked (active)
    existing = await session.scalar(
        select(UserEmployeeLink).where(
            (UserEmployeeLink.user_id == user_id) | (UserEmployeeLink.employee_id == employee_id),
            UserEmployeeLink.is_active.is_(True),
        )
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User or Employee already linked")

    link = UserEmployeeLink(user_id=user_id, employee_id=employee_id, business_id=employee.business_id, created_by=actor.user_id)
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link
