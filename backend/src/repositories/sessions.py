"""
Repository for browser_sessions table.
"""
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select

from config.logging import get_database_logger
from src.models.session import BrowserSession
from src.repositories.base import BaseRepository

logger = get_database_logger()


def _row_to_dict(row: BrowserSession) -> Dict[str, Any]:
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


class SessionRepository(BaseRepository):
    """Data access layer for the browser_sessions table."""

    async def create(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a new browser session and return the full record."""
        try:
            session = BrowserSession(**session_data)
            self._session.add(session)
            await self._session.flush()
            return _row_to_dict(session)
        except Exception as e:
            self._handle_db_error(e, "create_session")

    async def get(self, token: str) -> Optional[Dict[str, Any]]:
        """Return an active, non-expired session by token, or None."""
        try:
            now = datetime.now(timezone.utc)
            result = await self._session.execute(
                select(BrowserSession)
                .where(
                    BrowserSession.session_token == token,
                    BrowserSession.is_active.is_(True),
                    BrowserSession.expires_at > now,
                )
            )
            row = result.scalar_one_or_none()
            return _row_to_dict(row) if row else None
        except Exception as e:
            logger.debug(f"Session {token[:8]}... not found: {e}")
            return None

    async def touch(self, token: str) -> None:
        """Update last_accessed_at timestamp for activity tracking."""
        try:
            result = await self._session.execute(
                select(BrowserSession).where(BrowserSession.session_token == token)
            )
            row = result.scalar_one_or_none()
            if row:
                row.last_accessed_at = datetime.now(timezone.utc)
                await self._session.flush()
        except Exception as e:
            logger.warning(f"Failed to touch session {token[:8]}...: {e}")
