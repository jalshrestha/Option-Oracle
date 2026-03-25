"""
Analysis routes — thin controllers.
All business logic lives in AnalysisService.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Path

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import (
    get_analysis_service,
    get_current_session,
    get_db,
    get_rate_limiter,
)
from src.repositories.signals import TradingSignalRepository
from src.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    RecentSignalItem,
    SignalSchema,
)
from src.services.analysis_service import AnalysisService

router = APIRouter()

_analyze_limit = get_rate_limiter(max_requests=30)
_default_limit = get_rate_limiter(max_requests=60)


@router.post("/analyze/{symbol}", response_model=AnalysisResponse)
async def analyze_stock(
    symbol: str = Path(..., min_length=1, max_length=5, pattern=r"^[A-Za-z]+$"),
    service: AnalysisService = Depends(get_analysis_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_analyze_limit),
) -> AnalysisResponse:
    """Run the full multi-agent analysis pipeline for *symbol*."""
    req = AnalysisRequest(symbol=symbol)
    risk_profile = {"risk_tolerance": session.get("risk_profile", "moderate")}
    return await service.analyze(req.symbol, risk_profile)


@router.get("/history/{symbol}", response_model=List[SignalSchema])
async def get_analysis_history(
    symbol: str,
    limit: int = 10,
    service: AnalysisService = Depends(get_analysis_service),
    session: Dict[str, Any] = Depends(get_current_session),
    _rl: None = Depends(_default_limit),
) -> List[SignalSchema]:
    """Return recent signals for *symbol*, newest first."""
    return await service.get_history(symbol.upper(), limit=limit)


@router.get("/signals/recent", response_model=List[RecentSignalItem])
async def get_recent_signals(
    limit: int = Query(default=20, ge=1, le=100),
    session: Dict[str, Any] = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(_default_limit),
) -> List[RecentSignalItem]:
    """Return the most recent trading signals across all symbols."""
    repo = TradingSignalRepository(db)
    rows = await repo.get_recent_all(limit=limit)
    items = []
    for row in rows:
        items.append(
            RecentSignalItem(
                id=str(row.get("id", "")),
                symbol=row.get("symbol", ""),
                direction=row.get("direction", "HOLD"),
                strength=row.get("strength"),
                confidence_score=float(row.get("confidence_score", 0.0)),
                market_scenario=row.get("market_scenario", "NEUTRAL"),
                created_at=(
                    row["created_at"].isoformat()
                    if row.get("created_at")
                    else None
                ),
            )
        )
    return items


@router.get("/symbols")
async def get_supported_symbols() -> Dict[str, Any]:
    """Return the list of symbols the platform supports."""
    return {
        "popular": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"],
        "options_enabled": True,
        "total_available": 5000,
    }
