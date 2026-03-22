"""
Repository for positions table.
All queries against this table are defined here.
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from config.logging import get_database_logger
from src.exceptions import NotFoundError
from src.models.position import Position
from src.repositories.base import BaseRepository

logger = get_database_logger()


def _row_to_dict(row: Position) -> Dict[str, Any]:
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


class PositionRepository(BaseRepository):
    """Data access layer for the positions table."""

    async def create(self, position_data: Dict[str, Any]) -> Optional[str]:
        """Insert a new position and return its ID."""
        try:
            position = Position(**position_data)
            self._session.add(position)
            await self._session.flush()
            return str(position.id)
        except Exception as e:
            self._handle_db_error(e, "create_position")

    async def update_pnl(self, position_id: str, pnl: float) -> None:
        """Update the unrealized P&L for an open position."""
        try:
            result = await self._session.execute(
                select(Position).where(Position.id == uuid.UUID(position_id))
            )
            pos = result.scalar_one_or_none()
            if pos:
                pos.unrealized_pnl = pnl
                await self._session.flush()
        except Exception as e:
            self._handle_db_error(e, f"update_pnl({position_id})")

    async def get_open(self, session_id: str) -> List[Dict[str, Any]]:
        """Return all open positions for a session."""
        try:
            result = await self._session.execute(
                select(Position)
                .where(Position.session_id == session_id, Position.status == "open")
                .order_by(Position.created_at.desc())
            )
            return [_row_to_dict(row) for row in result.scalars().all()]
        except Exception as e:
            self._handle_db_error(e, f"get_open({session_id})")

    async def get_by_id(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Return a single position by ID, or None."""
        try:
            result = await self._session.execute(
                select(Position).where(Position.id == uuid.UUID(position_id))
            )
            row = result.scalar_one_or_none()
            return _row_to_dict(row) if row else None
        except Exception as e:
            logger.debug(f"Position {position_id} not found: {e}")
            return None

    async def close(self, position_id: str) -> Dict[str, Any]:
        """Mark a position as closed and return the updated record."""
        try:
            result = await self._session.execute(
                select(Position).where(Position.id == uuid.UUID(position_id))
            )
            pos = result.scalar_one_or_none()
            if not pos:
                raise NotFoundError(f"Position {position_id} not found")
            pos.status = "closed"
            pos.closed_at = datetime.now(timezone.utc)
            await self._session.flush()
            return _row_to_dict(pos)
        except NotFoundError:
            raise
        except Exception as e:
            self._handle_db_error(e, f"close_position({position_id})")
