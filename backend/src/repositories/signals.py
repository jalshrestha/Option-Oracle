"""
Repository for trading_signals table.
All queries against this table are defined here.
"""
import json
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from config.logging import get_database_logger
from src.models.signal import TradingSignal
from src.repositories.base import BaseRepository

logger = get_database_logger()
TRADING_SIGNAL_COLUMNS = {column.name for column in TradingSignal.__table__.columns}


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
            normalized = self._normalize_signal_data(signal_data)
            signal = TradingSignal(**normalized)
            self._session.add(signal)
            await self._session.flush()
            return str(signal.id)
        except Exception as e:
            self._handle_db_error(e, "save_signal")

    def _normalize_signal_data(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Drop legacy keys and fill required model fields for signal persistence."""
        normalized = {
            key: value
            for key, value in signal_data.items()
            if key in TRADING_SIGNAL_COLUMNS
        }
        normalized.setdefault("decision_score", 0.0)
        normalized.setdefault("strategy_type", signal_data.get("signal_type", "hybrid"))
        normalized.setdefault("reasoning", "")
        normalized.setdefault("agent_weights", {})
        normalized.setdefault("technical_analysis", {})
        normalized.setdefault("sentiment_analysis", {})
        normalized.setdefault("flow_analysis", {})
        normalized.setdefault("historical_analysis", {})
        normalized.setdefault("strike_recommendations", [])
        normalized.setdefault("educational_content", "")
        if not isinstance(normalized.get("educational_content"), str):
            normalized["educational_content"] = json.dumps(
                normalized["educational_content"],
                default=str,
            )
        return normalized

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

    async def get_recent_all(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent signals across all symbols, newest first."""
        try:
            result = await self._session.execute(
                select(TradingSignal)
                .order_by(TradingSignal.created_at.desc())
                .limit(limit)
            )
            return [_row_to_dict(row) for row in result.scalars().all()]
        except Exception as e:
            self._handle_db_error(e, "get_recent_all")
