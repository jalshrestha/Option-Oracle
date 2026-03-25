"""
Option Oracle — Database Configuration

Provides:
- Async SQLAlchemy engine backed by PostgreSQL 16
- Per-request AsyncSession via async_sessionmaker
- health_check() for /health endpoint
- create_tables() for development startup (Alembic handles production)
"""
from typing import Any, Dict

from loguru import logger
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config.settings import settings


# ---------------------------------------------------------------------------
# Engine — created once at module import time
# ---------------------------------------------------------------------------
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=settings.db_connect_timeout,
    pool_recycle=3600,
    pool_pre_ping=True,          # detect stale connections
    echo=(settings.app_debug and settings.env == "development"),
)

# ---------------------------------------------------------------------------
# Session factory — used by get_db() in dependencies.py
# ---------------------------------------------------------------------------
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Startup helpers
# ---------------------------------------------------------------------------

async def create_tables() -> None:
    """
    Create all tables defined in src/models/.

    Used in development (ENV != 'production').
    In production, Alembic migrations manage the schema — do not call this.
    """
    from src.models import Base  # local import avoids circular dependency at module load

    logger.info("Creating database tables (development mode)...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")


async def health_check() -> Dict[str, Any]:
    """
    Verify database connectivity.

    Returns a dict with 'status' key: 'healthy' or 'unhealthy'.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "connection": "active", "backend": "postgresql"}
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return {"status": "unhealthy", "connection": "failed", "error": str(exc)}
