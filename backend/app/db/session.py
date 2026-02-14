from typing import AsyncGenerator

from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_POOL_SIZE,  # Max number of permanent connections
    max_overflow=settings.DATABASE_MAX_OVERFLOW,  # Max number of connections above pool_size
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,  # Seconds to wait for connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour (prevents stale connections)
)


# Dependency to get async session
async def get_async_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session


async def verify_connection(target_engine=None, db_url: str = "") -> None:
    """Verify database is reachable. Reusable for both app and test setup."""
    from sqlalchemy import text

    target_engine = target_engine or engine
    db_url = db_url or settings.DATABASE_URL

    try:
        async with AsyncSession(target_engine) as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        raise ConnectionError(
            f"\nCould not connect to database.\n\n"
            f"Check:\n"
            f"  1. PostgreSQL is running\n"
            f"  2. Database exists\n"
            f"  3. Credentials in .env (or .env.test) are correct\n\n"
            f"Error: {e}"
        ) from e
