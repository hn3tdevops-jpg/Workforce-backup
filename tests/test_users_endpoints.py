import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    email = f"ui-{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        "/api/v1/users/",
        json={
            "email": email,
            "first_name": "Test",
            "last_name": "User",
            "phone": "+123",
            "job_title": "Tester",
            "is_active": True,
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["email"] == email

    user = await db_session.scalar(select(User).where(User.email == email))
    assert user is not None
