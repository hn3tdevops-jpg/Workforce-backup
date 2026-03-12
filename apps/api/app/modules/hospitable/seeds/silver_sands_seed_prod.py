"""
Production seed script — idempotent.
Only seeds if no business named 'Silver Sands Motel' exists yet.
"""
from __future__ import annotations
import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from apps.api.app.db.base import import_models
from apps.api.app.models.tenant import Business
from apps.api.app.modules.hospitable.seeds.silver_sands_seed import seed_silver_sands

log = logging.getLogger(__name__)

async def _main() -> None:
    import_models()
    from apps.api.app.core.config import get_settings
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Business).where(Business.name == "Silver Sands Motel"))
        if existing.scalar_one_or_none():
            log.info("Silver Sands already seeded — skipping.")
        else:
            result = await seed_silver_sands(session)
            log.info("Seeded: %s", result)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(_main())
