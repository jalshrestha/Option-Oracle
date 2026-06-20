"""Schemas for the paper-trading domain."""
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class OptionDetails(BaseModel):
    """Option-specific fields required when action involves options."""

    option_type: Literal["call", "put"]
    strike: float = Field(..., gt=0)
    expiry: str = Field(..., description="Expiry date in YYYY-MM-DD format")


class TradeRequest(BaseModel):
    """Request body for executing a paper trade."""

    model_config = ConfigDict(frozen=True)

    symbol: str
    action: Literal["buy", "sell"]
    quantity: int = Field(..., ge=1)
    order_type: Literal["market", "limit"] = "market"
    limit_price: Optional[float] = Field(default=None, gt=0)
    option_details: Optional[OptionDetails] = None

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @model_validator(mode="after")
    def limit_price_required_for_limit_orders(self) -> "TradeRequest":
        if self.order_type == "limit" and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        return self


class TradeResponse(BaseModel):
    """Response after a paper trade is executed."""

    trade_id: str
    status: Literal["executed", "failed", "simulated"]
    position_id: Optional[str] = None
    execution_price: Optional[float] = None
    message: str = ""


class PositionSchema(BaseModel):
    """A single open or closed position."""

    id: str
    symbol: str
    option_type: Optional[str] = None
    strike_price: Optional[float] = None
    expiry_date: Optional[str] = None
    quantity: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    status: Literal["open", "closed"]
    greeks: Optional[Dict[str, float]] = None


class AnalyzeBuyRequest(BaseModel):
    """Request body for creating a trade recommendation."""

    symbol: str
    user_query: Optional[str] = None
    risk_profile: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.strip().upper()


class RecommendationLeg(BaseModel):
    """Single recommendation leg."""

    asset_type: Literal["stock", "option"] = "option"
    action: Literal["buy", "sell"] = "buy"
    quantity: int = Field(..., ge=1)
    option_type: Optional[Literal["call", "put"]] = None
    strike: Optional[float] = Field(default=None, gt=0)
    expiry: Optional[str] = None
    estimated_price: float = Field(..., ge=0)


class TradeRecommendationResponse(BaseModel):
    """Persisted trade recommendation snapshot."""

    id: str
    symbol: str
    strategy: str
    action: Literal["buy", "sell"]
    status: Literal["draft", "confirmed", "executed", "expired", "rejected"]
    mode: Literal["paper", "live"]
    legs: List[RecommendationLeg]
    rationale: str
    source: str
    source_analysis_id: Optional[str] = None
    estimated_cost: float
    max_loss: float
    confidence: float
    risk_score: float
    expires_at: datetime
    executed_position_id: Optional[str] = None
    created_at: Optional[datetime] = None


class ExecuteRecommendationRequest(BaseModel):
    """Execute a persisted trade recommendation."""

    recommendation_id: str
    mode: Literal["paper", "live"] = "paper"
    confirmed: bool = False
    quantity: Optional[int] = Field(default=None, ge=1)
