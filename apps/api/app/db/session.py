from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.app.core.config import get_settings


def _make_engine():
    settings = get_settings()
    connect_args = {}
    database_url = settings.DATABASE_URL

    # If using SQLite without an async driver in the URL (e.g. "sqlite://" or "sqlite:///./dev.db"),
    # switch to the aiosqlite async driver for compatibility with SQLAlchemy asyncio extension.
    if database_url.startswith("sqlite") and "+" not in database_url:
        database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        connect_args = {"check_same_thread": False}
    elif database_url.startswith("sqlite"):
        # URL already contains a driver (e.g. sqlite+aiosqlite://) — still set sqlite-specific args.
        connect_args = {"check_same_thread": False}

    return create_async_engine(
        database_url,
        echo=False,
        future=True,
        connect_args=connect_args,
    )


engine = _make_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
