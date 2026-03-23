"""
Schemas for the portfolio domain.
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class GreeksSchema(BaseModel):
    """Aggregated portfolio Greeks."""

    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0


class RiskMetricsResponse(BaseModel):
    """Portfolio risk summary."""

    var_95: float = Field(default=0.0, description="95% Value at Risk")
    max_loss: float = 0.0
    beta: float = 1.0
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None


class PortfolioSummaryResponse(BaseModel):
    """Top-level portfolio summary."""

    total_value: float
    cash_balance: float
    unrealized_pnl: float
    realized_pnl: float
    open_positions: int
    total_return_pct: float
    greeks: GreeksSchema
    risk_metrics: RiskMetricsResponse
    allocation: Dict[str, float] = {}
