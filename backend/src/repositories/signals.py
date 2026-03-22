"""
Repository for trading_signals table.
All queries against this table are defined here.
"""
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from config.logging import get_database_logger
from src.models.signal import TradingSignal
from src.repositories.base import BaseRepository

logger = get_database_logger()


def _row_to_dict(row: TradingSignal) -> Dict[str, Any]:
    """Convert a TradingSignal ORM row to a plain dict, excluding SQLAlchemy internals."""
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


class TradingSignalRepository(BaseRepository):
    """Data access layer for the trading_signals table."""

    async def save(self, signal_data: Dict[str, Any]) -> Optional[str]:
        """
        Insert a new trading signal record.

        Returns the record ID (str) if available, otherwise None.
        Raises DatabaseError on failure.
        """
        try:
            signal = TradingSignal(**signal_data)
            self._session.add(signal)
            await self._session.flush()
            return str(signal.id)
        except Exception as e:
            self._handle_db_error(e, "save_signal")

    async def get_by_symbol(
        self, symbol: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return the most recent signals for a symbol, newest first."""
        try:
            result = await self._session.execute(
                select(TradingSignal)
                .where(TradingSignal.symbol == symbol.upper())
                .order_by(TradingSignal.created_at.desc())
                .limit(limit)
            )
            return [_row_to_dict(row) for row in result.scalars().all()]
        except Exception as e:
            self._handle_db_error(e, f"get_by_symbol({symbol})")

    async def get_latest(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return the single most recent signal for a symbol, or None."""
        records = await self.get_by_symbol(symbol, limit=1)
        return records[0] if records else None
