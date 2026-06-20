"""
Trading routes — thin controllers.
Mutations (execute, close) are handled by TradingService.
Read operations (positions list, portfolio summary) delegate to PortfolioService.
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from src.api.dependencies import (
    get_current_session,
    get_portfolio_service,
    get_rate_limiter,
    get_trading_service,
)
from src.schemas.trading import (
    AnalyzeBuyRequest,
    ExecuteRecommendationRequest,
    PositionSchema,
    TradeRecommendationResponse,
    TradeRequest,
    TradeResponse,
)
from src.services.portfolio_service import PortfolioService
from src.services.trading_service import TradingService

router = APIRouter()

_trade_limit = get_rate_limiter(max_requests=20)
_default_limit = get_rate_limiter(max_requests=60)


# ---------------------------------------------------------------------------
# Mutation endpoints
# ---------------------------------------------------------------------------

@router.post("/execute", response_model=TradeResponse)
async def execute_paper_trade(
    trade_request: TradeRequest,
    service: TradingService = Depends(get_trading_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_trade_limit),
) -> TradeResponse:
    """Execute a paper trade and open a new position."""
    return await service.execute_trade(trade_request, session["session_token"])


@router.post("/analyze-buy", response_model=TradeRecommendationResponse)
async def analyze_buy_recommendation(
    request: AnalyzeBuyRequest,
    service: TradingService = Depends(get_trading_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_trade_limit),
) -> TradeRecommendationResponse:
    """Create and persist a trade recommendation snapshot."""
    return await service.analyze_buy(request, session["session_token"])


@router.post("/execute-recommendation", response_model=TradeResponse)
async def execute_trade_recommendation(
    request: ExecuteRecommendationRequest,
    service: TradingService = Depends(get_trading_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_trade_limit),
) -> TradeResponse:
    """Execute a persisted recommendation after explicit confirmation."""
    return await service.execute_recommendation(request, session["session_token"])


@router.post("/positions/{position_id}/close", response_model=PositionSchema)
async def close_position(
    position_id: str,
    service: TradingService = Depends(get_trading_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_trade_limit),
) -> PositionSchema:
    """Close an open position by ID."""
    return await service.close_position(position_id, session["session_token"])


# ---------------------------------------------------------------------------
# Read endpoints
# ---------------------------------------------------------------------------

@router.get("/positions")
async def get_positions(
    service: PortfolioService = Depends(get_portfolio_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_default_limit),
) -> List[Dict[str, Any]]:
    """Return open positions for the current session."""
    return await service.get_open_positions(session["session_token"])


@router.get("/buy-recommendations/{symbol}", response_model=List[TradeRecommendationResponse])
async def get_buy_recommendations(
    symbol: str,
    service: TradingService = Depends(get_trading_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_default_limit),
) -> List[TradeRecommendationResponse]:
    """Return trade recommendations for the current session and symbol."""
    return await service.list_buy_recommendations(symbol, session["session_token"])


@router.get("/portfolio/summary")
async def get_portfolio_summary(
    service: PortfolioService = Depends(get_portfolio_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_default_limit),
) -> Dict[str, Any]:
    """Return a high-level portfolio summary for the current session."""
    return (await service.get_summary(session["session_token"])).model_dump()


@router.get("/orders")
async def get_orders(
    limit: int = 20,
    session: Dict[str, Any] = Depends(get_current_session),
) -> List[Dict[str, Any]]:
    """Return recent order history (stub — full implementation in a future phase)."""
    return []
