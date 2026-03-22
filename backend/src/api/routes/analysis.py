"""
Analysis routes — thin controllers.
All business logic lives in AnalysisService.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from src.api.dependencies import (
    get_analysis_service,
    get_current_session,
    get_rate_limiter,
)
from src.schemas.analysis import AnalysisRequest, AnalysisResponse, SignalSchema
from src.services.analysis_service import AnalysisService

router = APIRouter()

_analyze_limit = get_rate_limiter(max_requests=30)
_default_limit = get_rate_limiter(max_requests=60)


@router.post("/analyze/{symbol}", response_model=AnalysisResponse)
async def analyze_stock(
    symbol: str,
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


@router.get("/symbols")
async def get_supported_symbols() -> Dict[str, Any]:
    """Return the list of symbols the platform supports."""
    return {
        "popular": ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"],
        "options_enabled": True,
        "total_available": 5000,
    }
