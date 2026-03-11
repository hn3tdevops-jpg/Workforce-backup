import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.security import hash_password
from apps.api.app.db.session import get_async_session
from apps.api.app.models.tenant import Business, Location
from apps.api.app.models.user import User

router = APIRouter()


class BootstrapRequest(BaseModel):
    admin_email: EmailStr
    admin_password: str
    business_name: str
    location_name: str


class BootstrapResponse(BaseModel):
    business_id: uuid.UUID
    location_id: uuid.UUID
    user_id: uuid.UUID


@router.post("/bootstrap", response_model=BootstrapResponse, status_code=status.HTTP_201_CREATED)
async def bootstrap(
    payload: BootstrapRequest,
    session: AsyncSession = Depends(get_async_session),
) -> BootstrapResponse:
    count_result = await session.execute(select(func.count()).select_from(User))
    user_count = count_result.scalar_one()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bootstrap is only allowed when no users exist.",
        )

    business = Business(name=payload.business_name, id=uuid.uuid4())
    session.add(business)
    await session.flush()

    location = Location(name=payload.location_name, business_id=business.id, id=uuid.uuid4())
    session.add(location)
    await session.flush()

    user = User(
        email=payload.admin_email,
        hashed_password=hash_password(payload.admin_password),
        business_id=business.id,
        id=uuid.uuid4(),
    )
    session.add(user)
    await session.commit()

    return BootstrapResponse(
        business_id=business.id,
        location_id=location.id,
        user_id=user.id,
    )
