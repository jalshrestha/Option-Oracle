"""
Schemas for the paper-trading domain.
"""
from typing import Dict, Literal, Optional

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
