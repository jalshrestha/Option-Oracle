"""
Portfolio routes — thin controllers.
Aggregation logic lives entirely in PortfolioService.
"""
from collections import defaultdict
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from src.api.dependencies import (
    get_current_session,
    get_db,
    get_portfolio_service,
    get_rate_limiter,
)
from src.repositories.positions import PositionRepository
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
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(_default_limit),
) -> Dict[str, Any]:
    """Return portfolio performance analytics from closed positions."""
    repo = PositionRepository(db)
    closed = await repo.get_closed(session["session_token"])

    if not closed:
        return {
            "period": period,
            "total_return": 0.0,
            "total_return_percent": 0.0,
            "win_rate": 0.0,
            "performance_history": [],
        }

    # Group realized P&L by calendar date, then build cumulative curve
    daily_pnl: Dict[str, float] = defaultdict(float)
    for pos in closed:
        closed_at = pos.get("closed_at")
        if closed_at is None:
            continue
        date_str = (
            closed_at.strftime("%Y-%m-%d")
            if hasattr(closed_at, "strftime")
            else str(closed_at)[:10]
        )
        daily_pnl[date_str] += float(pos.get("realized_pnl", 0.0))

    cumulative = 0.0
    performance_history = []
    for date in sorted(daily_pnl):
        cumulative += daily_pnl[date]
        performance_history.append({"date": date, "value": round(cumulative, 2)})

    total_return = sum(float(p.get("realized_pnl", 0.0)) for p in closed)
    winning = sum(1 for p in closed if float(p.get("realized_pnl", 0.0)) > 0)
    win_rate = (winning / len(closed) * 100) if closed else 0.0
    balance = settings.paper_trading_balance or 100_000.0
    total_return_percent = total_return / balance * 100

    return {
        "period": period,
        "total_return": round(total_return, 2),
        "total_return_percent": round(total_return_percent, 2),
        "win_rate": round(win_rate, 1),
        "performance_history": performance_history,
    }


@router.get("/alerts")
async def get_portfolio_alerts(
    session: Dict[str, Any] = Depends(get_current_session),
) -> List[Dict[str, Any]]:
    """Return active portfolio alerts (stub)."""
    return []
