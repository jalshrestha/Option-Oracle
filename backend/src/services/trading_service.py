"""
TradingService — paper-trade execution and position lifecycle.

Rules:
  - No direct DB access. Uses PositionRepository only.
  - No HTTP concerns.
  - P&L calculation lives here, not in config/database.py.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from config.logging import get_api_logger
from config.settings import settings
from src.exceptions import NotFoundError, ValidationError
from src.repositories.positions import PositionRepository
from src.repositories.trade_recommendations import TradeRecommendationRepository
from src.schemas.trading import (
    AnalyzeBuyRequest,
    ExecuteRecommendationRequest,
    OptionDetails,
    PositionSchema,
    RecommendationLeg,
    TradeRecommendationResponse,
    TradeRequest,
    TradeResponse,
)

logger = get_api_logger()

# Options contract multiplier: 1 contract = 100 shares
OPTION_MULTIPLIER = 100


class TradingService:
    """Business logic for paper trade execution and position management."""

    def __init__(
        self,
        position_repo: PositionRepository,
        recommendation_repo: TradeRecommendationRepository | None = None,
    ) -> None:
        self._position_repo = position_repo
        self._recommendation_repo = recommendation_repo

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

    async def close_position(self, position_id: str, session_id: str) -> PositionSchema:
        """
        Close an open position and return the updated schema.

        Raises NotFoundError if the position does not exist.
        """
        existing = await self._position_repo.get_by_id(position_id, session_id=session_id)
        if not existing:
            raise NotFoundError(f"Position {position_id} not found")

        updated = await self._position_repo.close(position_id, session_id=session_id)
        record = updated or existing
        return self._to_schema(record)

    async def refresh_pnl(
        self,
        position_id: str,
        session_id: str,
        current_price: float,
    ) -> float:
        """
        Recalculate and persist P&L for a position given the current market price.

        Returns the new unrealized P&L value.
        """
        position = await self._position_repo.get_by_id(position_id, session_id=session_id)
        if not position:
            raise NotFoundError(f"Position {position_id} not found")

        entry = position.get("entry_price", 0.0)
        qty = position.get("quantity", 1)
        is_option = bool(position.get("option_type"))
        multiplier = OPTION_MULTIPLIER if is_option else 1

        pnl = (current_price - entry) * qty * multiplier
        await self._position_repo.update_pnl(position_id, pnl, session_id=session_id)
        return pnl

    async def analyze_buy(
        self, request: AnalyzeBuyRequest, session_id: str
    ) -> TradeRecommendationResponse:
        """Create a persisted paper-trading recommendation snapshot."""
        repo = self._require_recommendation_repo()
        risk_profile = request.risk_profile or {}
        account_balance = float(risk_profile.get("account_balance", settings.paper_trading_balance))
        max_position_pct = float(risk_profile.get("max_position_size", 0.05))
        max_trade_value = max(account_balance * max_position_pct, 100.0)
        estimated_price = min(max(max_trade_value / OPTION_MULTIPLIER, 1.0), 10.0)
        strike = float(risk_profile.get("target_strike", 100.0))
        option_type = "put" if "put" in (request.user_query or "").lower() else "call"
        strategy = "long_put" if option_type == "put" else "long_call"
        quantity = max(1, int(max_trade_value // (estimated_price * OPTION_MULTIPLIER)))
        estimated_cost = estimated_price * quantity * OPTION_MULTIPLIER

        data = {
            "session_id": session_id,
            "symbol": request.symbol,
            "strategy": strategy,
            "action": "buy",
            "status": "draft",
            "mode": "paper",
            "legs": [
                {
                    "asset_type": "option",
                    "action": "buy",
                    "quantity": quantity,
                    "option_type": option_type,
                    "strike": strike,
                    "expiry": risk_profile.get("expiry", self._default_expiry()),
                    "estimated_price": estimated_price,
                }
            ],
            "rationale": (
                "Rule-based starter recommendation. Use valid market/AI keys for richer "
                "signal-backed recommendations."
            ),
            "source": "rule_based",
            "source_analysis_id": None,
            "estimated_cost": estimated_cost,
            "max_loss": estimated_cost,
            "confidence": 0.5,
            "risk_score": min(1.0, estimated_cost / max(account_balance, 1.0)),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
        }
        return self._recommendation_to_schema(await repo.create(data))

    async def list_buy_recommendations(
        self, symbol: str, session_id: str
    ) -> list[TradeRecommendationResponse]:
        """Return persisted recommendations for the current session and symbol."""
        rows = await self._require_recommendation_repo().list_for_symbol(session_id, symbol)
        return [self._recommendation_to_schema(row) for row in rows]

    async def execute_recommendation(
        self, request: ExecuteRecommendationRequest, session_id: str
    ) -> TradeResponse:
        """Execute a persisted recommendation after explicit confirmation."""
        if not request.confirmed:
            raise ValidationError("Recommendation execution requires confirmed=true")
        if request.mode == "live" and not settings.live_trading_enabled:
            raise ValidationError("Live trading is disabled")

        repo = self._require_recommendation_repo()
        rec = await repo.get_by_id(request.recommendation_id, session_id)
        if not rec:
            raise NotFoundError("Trade recommendation not found")
        if rec.get("status") not in {"draft", "confirmed"}:
            raise ValidationError("Trade recommendation is not executable")

        expires_at = rec.get("expires_at")
        if expires_at and expires_at < datetime.now(timezone.utc):
            raise ValidationError("Trade recommendation has expired")

        legs = rec.get("legs") or []
        if not legs:
            raise ValidationError("Trade recommendation has no executable legs")
        leg = legs[0]
        quantity = request.quantity or int(leg.get("quantity", 1))
        trade_request = TradeRequest(
            symbol=rec["symbol"],
            action=leg.get("action", "buy"),
            quantity=quantity,
            order_type="limit",
            limit_price=float(leg.get("estimated_price", 0.0)) or 1.0,
            option_details=OptionDetails(
                option_type=leg.get("option_type", "call"),
                strike=float(leg.get("strike", 1.0)),
                expiry=leg.get("expiry") or self._default_expiry(),
            ) if leg.get("asset_type") == "option" else None,
        )
        response = await self.execute_trade(trade_request, session_id)
        await repo.mark_executed(request.recommendation_id, session_id, response.position_id)
        return response

    # ------------------------------------------------------------------

    @staticmethod
    def _to_schema(record: Dict[str, Any]) -> PositionSchema:
        return PositionSchema(
            id=str(record.get("id", "")),
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

    def _require_recommendation_repo(self) -> TradeRecommendationRepository:
        if not self._recommendation_repo:
            raise ValidationError("Trade recommendations are not configured")
        return self._recommendation_repo

    @staticmethod
    def _recommendation_to_schema(record: Dict[str, Any]) -> TradeRecommendationResponse:
        return TradeRecommendationResponse(
            id=str(record["id"]),
            symbol=record["symbol"],
            strategy=record["strategy"],
            action=record["action"],
            status=record["status"],
            mode=record["mode"],
            legs=[RecommendationLeg(**leg) for leg in record.get("legs", [])],
            rationale=record["rationale"],
            source=record["source"],
            source_analysis_id=record.get("source_analysis_id"),
            estimated_cost=record.get("estimated_cost", 0.0),
            max_loss=record.get("max_loss", 0.0),
            confidence=record.get("confidence", 0.0),
            risk_score=record.get("risk_score", 0.5),
            expires_at=record["expires_at"],
            executed_position_id=record.get("executed_position_id"),
            created_at=record.get("created_at"),
        )

    @staticmethod
    def _default_expiry() -> str:
        return (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
