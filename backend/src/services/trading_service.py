"""
TradingService — paper-trade execution and position lifecycle.

Rules:
  - No direct DB access. Uses PositionRepository only.
  - No HTTP concerns.
  - P&L calculation lives here, not in config/database.py.
"""
import uuid
from datetime import datetime
from typing import Any, Dict

from config.logging import get_api_logger
from src.exceptions import DatabaseError, NotFoundError
from src.repositories.positions import PositionRepository
from src.schemas.trading import PositionSchema, TradeRequest, TradeResponse

logger = get_api_logger()

# Options contract multiplier: 1 contract = 100 shares
OPTION_MULTIPLIER = 100


class TradingService:
    """Business logic for paper trade execution and position management."""

    def __init__(self, position_repo: PositionRepository) -> None:
        self._position_repo = position_repo

    async def execute_trade(
        self, request: TradeRequest, session_id: str
    ) -> TradeResponse:
        """
        Execute a paper trade and open a new position.

        Returns a TradeResponse with the generated position ID.
        Raises DatabaseError if the position cannot be persisted.
        """
        trade_id = str(uuid.uuid4())
        position_data = {
            "session_id": session_id,
            "symbol": request.symbol,
            "quantity": request.quantity,
            "entry_price": request.limit_price or 0.0,
            "current_price": request.limit_price or 0.0,
            "unrealized_pnl": 0.0,
            "status": "open",
            "created_at": datetime.now().isoformat(),
        }

        if request.option_details:
            opt = request.option_details
            position_data.update(
                {
                    "option_type": opt.option_type,
                    "strike_price": opt.strike,
                    "expiry_date": opt.expiry,
                }
            )

        position_id = await self._position_repo.create(position_data)

        return TradeResponse(
            trade_id=trade_id,
            status="executed",
            position_id=position_id,
            execution_price=request.limit_price,
            message=f"Paper trade executed for {request.symbol}",
        )

    async def close_position(self, position_id: str) -> PositionSchema:
        """
        Close an open position and return the updated schema.

        Raises NotFoundError if the position does not exist.
        """
        existing = await self._position_repo.get_by_id(position_id)
        if not existing:
            raise NotFoundError(f"Position {position_id} not found")

        updated = await self._position_repo.close(position_id)
        record = updated or existing
        return self._to_schema(record)

    async def refresh_pnl(
        self,
        position_id: str,
        current_price: float,
    ) -> float:
        """
        Recalculate and persist P&L for a position given the current market price.

        Returns the new unrealized P&L value.
        """
        position = await self._position_repo.get_by_id(position_id)
        if not position:
            raise NotFoundError(f"Position {position_id} not found")

        entry = position.get("entry_price", 0.0)
        qty = position.get("quantity", 1)
        is_option = bool(position.get("option_type"))
        multiplier = OPTION_MULTIPLIER if is_option else 1

        pnl = (current_price - entry) * qty * multiplier
        await self._position_repo.update_pnl(position_id, pnl)
        return pnl

    # ------------------------------------------------------------------

    @staticmethod
    def _to_schema(record: Dict[str, Any]) -> PositionSchema:
        return PositionSchema(
            id=record.get("id", ""),
            symbol=record.get("symbol", ""),
            option_type=record.get("option_type"),
            strike_price=record.get("strike_price"),
            expiry_date=record.get("expiry_date"),
            quantity=record.get("quantity", 0),
            entry_price=record.get("entry_price", 0.0),
            current_price=record.get("current_price", 0.0),
            unrealized_pnl=record.get("unrealized_pnl", 0.0),
            status=record.get("status", "open"),
        )
