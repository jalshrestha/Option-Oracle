"""
Portfolio routes — thin controllers.
Aggregation logic lives entirely in PortfolioService.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from src.api.dependencies import (
    get_current_session,
    get_portfolio_service,
    get_rate_limiter,
)
from src.schemas.portfolio import GreeksSchema, PortfolioSummaryResponse, RiskMetricsResponse
from src.services.portfolio_service import PortfolioService

router = APIRouter()

_default_limit = get_rate_limiter(max_requests=60)


@router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    service: PortfolioService = Depends(get_portfolio_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_default_limit),
) -> PortfolioSummaryResponse:
    """Return a full portfolio summary for the current session."""
    return await service.get_summary(session["session_token"])


@router.get("/greeks", response_model=GreeksSchema)
async def get_portfolio_greeks(
    service: PortfolioService = Depends(get_portfolio_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_default_limit),
) -> GreeksSchema:
    """Return aggregated option Greeks for all open positions."""
    return await service.get_greeks(session["session_token"])


@router.get("/risk", response_model=RiskMetricsResponse)
async def get_risk_metrics(
    service: PortfolioService = Depends(get_portfolio_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_default_limit),
) -> RiskMetricsResponse:
    """Return VaR and max-loss risk metrics for the current session."""
    return await service.get_risk_metrics(session["session_token"])


@router.get("/positions")
async def get_portfolio_positions(
    service: PortfolioService = Depends(get_portfolio_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_default_limit),
) -> Dict[str, Any]:
    """Return open positions embedded in the full portfolio summary."""
    summary = await service.get_summary(session["session_token"])
    return {
        "open_positions": summary.open_positions,
        "allocation": summary.allocation,
    }


@router.get("/performance")
async def get_portfolio_performance(
    period: str = "1M",
    session: Dict[str, Any] = Depends(get_current_session),
) -> Dict[str, Any]:
    """Return portfolio performance analytics (stub)."""
    return {
        "period": period,
        "total_return": 0.0,
        "total_return_percent": 0.0,
        "win_rate": 0.0,
        "note": "Full performance history coming in a future phase.",
    }


@router.get("/alerts")
async def get_portfolio_alerts(
    session: Dict[str, Any] = Depends(get_current_session),
) -> List[Dict[str, Any]]:
    """Return active portfolio alerts (stub)."""
    return []
