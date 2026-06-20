"""Repository for trade recommendations."""
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from src.exceptions import NotFoundError
from src.models.trade_recommendation import TradeRecommendation
from src.repositories.base import BaseRepository


def _row_to_dict(row: TradeRecommendation) -> Dict[str, Any]:
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


class TradeRecommendationRepository(BaseRepository):
    """Data access layer for persisted trade recommendations."""

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rec = TradeRecommendation(**data)
            self._session.add(rec)
            await self._session.flush()
            await self._session.refresh(rec)
            return _row_to_dict(rec)
        except Exception as e:
            self._handle_db_error(e, "create_trade_recommendation")

    async def list_for_symbol(self, session_id: str, symbol: str) -> List[Dict[str, Any]]:
        try:
            result = await self._session.execute(
                select(TradeRecommendation)
                .where(
                    TradeRecommendation.session_id == session_id,
                    TradeRecommendation.symbol == symbol.upper(),
                )
                .order_by(TradeRecommendation.created_at.desc())
            )
            return [_row_to_dict(row) for row in result.scalars().all()]
        except Exception as e:
            self._handle_db_error(e, f"list_recommendations({session_id},{symbol})")

    async def get_by_id(self, recommendation_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            result = await self._session.execute(
                select(TradeRecommendation).where(
                    TradeRecommendation.id == uuid.UUID(recommendation_id),
                    TradeRecommendation.session_id == session_id,
                )
            )
            row = result.scalar_one_or_none()
            return _row_to_dict(row) if row else None
        except ValueError:
            return None
        except Exception as e:
            self._handle_db_error(e, f"get_recommendation({recommendation_id})")

    async def mark_executed(
        self, recommendation_id: str, session_id: str, position_id: Optional[str]
    ) -> Dict[str, Any]:
        try:
            result = await self._session.execute(
                select(TradeRecommendation).where(
                    TradeRecommendation.id == uuid.UUID(recommendation_id),
                    TradeRecommendation.session_id == session_id,
                )
            )
            row = result.scalar_one_or_none()
            if not row:
                raise NotFoundError("Trade recommendation not found")
            row.status = "executed"
            row.executed_position_id = position_id
            await self._session.flush()
            await self._session.refresh(row)
            return _row_to_dict(row)
        except NotFoundError:
            raise
        except Exception as e:
            self._handle_db_error(e, f"mark_recommendation_executed({recommendation_id})")
