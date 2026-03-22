"""
Repository for stocks table.
"""
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from config.logging import get_database_logger
from src.models.stock import Stock
from src.repositories.base import BaseRepository

logger = get_database_logger()


def _row_to_dict(row: Stock) -> Dict[str, Any]:
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


class StockRepository(BaseRepository):
    """Data access layer for the stocks table."""

    async def upsert_batch(self, stocks: List[Dict[str, Any]]) -> None:
        """Upsert a batch of stock records (insert or update by symbol)."""
        if not stocks:
            return
        try:
            stmt = pg_insert(Stock).values(stocks)
            stmt = stmt.on_conflict_do_update(
                index_elements=["symbol"],
                set_={
                    "company_name": stmt.excluded.company_name,
                    "sector": stmt.excluded.sector,
                    "market_cap": stmt.excluded.market_cap,
                    "volume": stmt.excluded.volume,
                },
            )
            await self._session.execute(stmt)
            await self._session.flush()
        except Exception as e:
            self._handle_db_error(e, "upsert_batch")

    async def get_trending(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return trending stocks ordered by volume (descending)."""
        try:
            result = await self._session.execute(
                select(Stock)
                .order_by(Stock.volume.desc().nulls_last())
                .limit(limit)
            )
            return [_row_to_dict(row) for row in result.scalars().all()]
        except Exception as e:
            self._handle_db_error(e, "get_trending")
