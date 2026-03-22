"""
Base repository providing shared DB-access helpers.

All repository classes inherit from BaseRepository and get:
- A reference to an AsyncSession
- A _handle_db_error() wrapper that converts raw SQLAlchemy exceptions
  into DatabaseError (never leaks internal details to callers)
"""
from sqlalchemy.ext.asyncio import AsyncSession

from config.logging import get_database_logger
from src.exceptions import DatabaseError

logger = get_database_logger()


class BaseRepository:
    """Thin base class for all repository implementations."""

    def __init__(self, session: AsyncSession) -> None:
        """
        Args:
            session: An AsyncSession scoped to the current HTTP request.
        """
        self._session = session

    def _handle_db_error(self, exc: Exception, context: str) -> None:
        """
        Log the raw exception and raise a DatabaseError in its place.

        Args:
            exc:     The original exception from SQLAlchemy / asyncpg.
            context: Short description of the operation (e.g. 'save_signal').
        """
        logger.error(f"DB error in {context}: {exc}")
        raise DatabaseError(f"Database operation failed: {context}") from exc
