"""
Integration tests for /api/v1/analysis/* routes.
Services are overridden via FastAPI dependency_overrides — no live DB or OpenAI needed.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient

from src.api.dependencies import get_analysis_service, get_current_session, get_rate_limiter
from src.schemas.analysis import AnalysisResponse, SignalSchema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_analysis_response(symbol: str = "AAPL") -> AnalysisResponse:
    from datetime import datetime
    from src.schemas.analysis import StrikeRecommendation
    signal = SignalSchema(
        direction="BUY",
        strength="moderate",
        confidence=0.72,
        decision_score=0.45,
        strategy_type="moderate_bullish",
        market_scenario="range_bound",
        reasoning="Strong momentum",
    )
    return AnalysisResponse(
        symbol=symbol,
        signal=signal,
        agent_results={"technical": {"weighted_score": 0.5}},
        strike_recommendations=[],
        educational_content="Test explanation.",
        confidence=0.72,
        market_scenario="range_bound",
        agent_weights={"technical": 0.6},
        analysis_time_seconds=5.2,
        timestamp=datetime.now().isoformat(),
    )


def _mock_session():
    return {"session_token": "test-token", "risk_profile": "moderate", "preferences": {}}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def analysis_app():
    """Return the FastAPI app with analysis service and session mocked out."""
    from src.api.main import app

    mock_service = AsyncMock()
    mock_service.analyze.return_value = _mock_analysis_response()
    mock_service.get_history.return_value = [
        SignalSchema(
            direction="BUY",
            strength="moderate",
            confidence=0.7,
            decision_score=0.4,
            strategy_type="hybrid",
            market_scenario="range_bound",
            reasoning="",
        )
    ]

    app.dependency_overrides[get_analysis_service] = lambda: mock_service
    app.dependency_overrides[get_current_session] = lambda: _mock_session()
    # Disable rate limiting in tests
    app.dependency_overrides[get_rate_limiter(max_requests=30)] = lambda: None
    app.dependency_overrides[get_rate_limiter(max_requests=60)] = lambda: None

    yield app, mock_service

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_check():
    from src.api.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Health check doesn't need session auth
        resp = await client.get("/health")
    assert resp.status_code in (200, 503)  # 503 if DB not available in test env


@pytest.mark.asyncio
async def test_analyze_stock_returns_200(analysis_app):
    app, mock_service = analysis_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/analysis/analyze/AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["signal"]["direction"] == "BUY"
    assert 0 <= data["confidence"] <= 1


@pytest.mark.asyncio
async def test_analyze_stock_calls_service(analysis_app):
    app, mock_service = analysis_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/api/v1/analysis/analyze/TSLA")
    mock_service.analyze.assert_called_once_with(
        "TSLA", {"risk_tolerance": "moderate"}
    )


@pytest.mark.asyncio
async def test_analyze_stock_invalid_symbol_raises_422(analysis_app):
    app, _ = analysis_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/analysis/analyze/TOOLONG")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_history_returns_200(analysis_app):
    app, mock_service = analysis_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/analysis/history/AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["direction"] == "BUY"


@pytest.mark.asyncio
async def test_get_history_calls_service_with_upper_symbol(analysis_app):
    app, mock_service = analysis_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.get("/api/v1/analysis/history/aapl")
    mock_service.get_history.assert_called_once_with("AAPL", limit=10)


@pytest.mark.asyncio
async def test_get_supported_symbols_returns_200():
    from src.api.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/analysis/symbols")
    assert resp.status_code == 200
    data = resp.json()
    assert "AAPL" in data["popular"]
