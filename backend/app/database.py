import asyncpg
from typing import AsyncGenerator, Optional
from app.config import settings


pool: Optional[asyncpg.Pool] = None


def _asyncpg_dsn(url: str) -> str:
    """Convert SQLAlchemy-style DSN (postgresql+asyncpg://...) to plain asyncpg DSN."""
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def create_pool() -> asyncpg.Pool:
    """Create and return an asyncpg connection pool."""
    global pool
    pool = await asyncpg.create_pool(
        dsn=_asyncpg_dsn(settings.DATABASE_URL),
        min_size=2,
        max_size=10,
        command_timeout=60,
    )
    return pool


async def close_pool() -> None:
    """Close the asyncpg connection pool."""
    global pool
    if pool is not None:
        await pool.close()
        pool = None


async def get_db() -> AsyncGenerator[asyncpg.Connection, None]:
    """FastAPI dependency: acquire a connection from the pool, yield, release."""
    global pool
    if pool is None:
        raise RuntimeError("Database pool is not initialised. Did lifespan run?")
    async with pool.acquire() as connection:
        yield connection
