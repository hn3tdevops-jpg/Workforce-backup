import uuid
from sqlalchemy import select
import pytest

from app.models.tenant import Business, Location


@pytest.mark.asyncio
async def test_business_location_crud(db_session) -> None:
    # Create business
    business = Business(name="AsyncCo")
    db_session.add(business)
    await db_session.flush()
    assert business.id is not None

    # Create location
    location = Location(name="HQ", business_id=business.id)
    db_session.add(location)
    await db_session.flush()
    assert location.id is not None

    # Read
    fetched = await db_session.scalar(select(Location).where(Location.id == location.id))
    assert fetched is not None
    assert fetched.business_id == business.id

    # Update
    fetched.name = "HQ Updated"
    db_session.add(fetched)
    await db_session.commit()
    fetched2 = await db_session.scalar(select(Location).where(Location.id == location.id))
    assert fetched2.name == "HQ Updated"

    # Delete
    await db_session.delete(fetched2)
    await db_session.commit()
    assert await db_session.scalar(select(Location).where(Location.id == location.id)) is None
