"""
PortfolioService — aggregated portfolio metrics.

Rules:
  - No direct DB access. Uses PositionRepository.
  - Greeks / risk calculations live here (moved from config/database.py).
"""
from typing import Any, Dict, List

from config.logging import get_api_logger
from config.settings import settings
from src.repositories.positions import PositionRepository
from src.schemas.portfolio import (
    GreeksSchema,
    PortfolioSummaryResponse,
    RiskMetricsResponse,
)

logger = get_api_logger()

OPTION_MULTIPLIER = 100


class PortfolioService:
    """Business logic for portfolio analytics."""

    def __init__(self, position_repo: PositionRepository) -> None:
        self._position_repo = position_repo

    async def get_summary(self, session_id: str) -> PortfolioSummaryResponse:
        """Return a full portfolio summary for the session."""
        positions = await self._position_repo.get_open(session_id)
        unrealized_pnl = sum(p.get("unrealized_pnl", 0.0) for p in positions)
        total_invested = sum(
            p.get("entry_price", 0.0)
            * p.get("quantity", 1)
            * (OPTION_MULTIPLIER if p.get("option_type") else 1)
            for p in positions
        )
        cash = settings.paper_trading_balance - total_invested
        total_value = cash + total_invested + unrealized_pnl
        return_pct = (unrealized_pnl / settings.paper_trading_balance) * 100 if settings.paper_trading_balance else 0.0

        return PortfolioSummaryResponse(
            total_value=max(total_value, 0.0),
            cash_balance=max(cash, 0.0),
            unrealized_pnl=unrealized_pnl,
            realized_pnl=0.0,
            open_positions=len(positions),
            total_return_pct=return_pct,
            greeks=self._aggregate_greeks(positions),
            risk_metrics=self._calculate_risk(positions, total_value),
            allocation=self._calculate_allocation(positions, total_value),
        )

    async def get_greeks(self, session_id: str) -> GreeksSchema:
        positions = await self._position_repo.get_open(session_id)
        return self._aggregate_greeks(positions)

    async def get_risk_metrics(self, session_id: str) -> RiskMetricsResponse:
        positions = await self._position_repo.get_open(session_id)
        total = sum(
            p.get("entry_price", 0.0) * p.get("quantity", 1)
            for p in positions
        )
        return self._calculate_risk(positions, total)

    # ------------------------------------------------------------------
    # Calculation helpers (pure functions — easy to test)
    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate_greeks(positions: List[Dict[str, Any]]) -> GreeksSchema:
        """Sum Greeks across all options positions."""
        delta = gamma = theta = vega = rho = 0.0
        for p in positions:
            if not p.get("option_type"):
                continue
            qty = p.get("quantity", 1)
            greeks = p.get("greeks") or {}
            delta += greeks.get("delta", 0.0) * qty
            gamma += greeks.get("gamma", 0.0) * qty
            theta += greeks.get("theta", 0.0) * qty
            vega += greeks.get("vega", 0.0) * qty
            rho += greeks.get("rho", 0.0) * qty
        return GreeksSchema(delta=delta, gamma=gamma, theta=theta, vega=vega, rho=rho)

    @staticmethod
    def _calculate_risk(
        positions: List[Dict[str, Any]], total_value: float
    ) -> RiskMetricsResponse:
        """Simple risk metrics — VaR approximation using 2% of total value."""
        if not positions or total_value <= 0:
            return RiskMetricsResponse()
        var_95 = total_value * 0.02
        max_loss = sum(
            p.get("entry_price", 0.0)
            * p.get("quantity", 1)
            * (OPTION_MULTIPLIER if p.get("option_type") else 1)
            for p in positions
        )
        return RiskMetricsResponse(var_95=var_95, max_loss=max_loss)

    @staticmethod
    def _calculate_allocation(
        positions: List[Dict[str, Any]], total_value: float
    ) -> Dict[str, float]:
        """Percentage allocation by symbol."""
        if total_value <= 0:
            return {}
        allocation: Dict[str, float] = {}
        for p in positions:
            symbol = p.get("symbol", "UNKNOWN")
            value = (
                p.get("entry_price", 0.0)
                * p.get("quantity", 1)
                * (OPTION_MULTIPLIER if p.get("option_type") else 1)
            )
            allocation[symbol] = allocation.get(symbol, 0.0) + (value / total_value * 100)
        return allocation
