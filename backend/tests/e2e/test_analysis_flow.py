"""
E2E test: analysis flow — HTTP POST → orchestrator (mocked) → signal saved to DB
(uses mocked DB + orchestrator so no live credentials required).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from src.api.dependencies import get_analysis_service, get_current_session, get_rate_limiter
from src.schemas.analysis import AnalysisResponse, SignalSchema


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def e2e_app():
    from src.api.main import app

    # Mock AnalysisService — simulates the full service layer
    mock_service = AsyncMock()

    from datetime import datetime
    signal = SignalSchema(
        direction="BUY",
        strength="moderate",
        confidence=0.72,
        decision_score=0.45,
        strategy_type="moderate_bullish",
        market_scenario="range_bound",
        reasoning="Strong momentum",
    )
    analysis_resp = AnalysisResponse(
        symbol="AAPL",
        signal=signal,
        agent_results={"technical": {"weighted_score": 0.5}},
        strike_recommendations=[],
        educational_content="Test.",
        confidence=0.72,
        market_scenario="range_bound",
        agent_weights={"technical": 0.6},
        analysis_time_seconds=5.1,
        timestamp=datetime.now().isoformat(),
    )
    mock_service.analyze.return_value = analysis_resp
    mock_service.get_history.return_value = [signal]

    app.dependency_overrides[get_analysis_service] = lambda: mock_service
    app.dependency_overrides[get_current_session] = lambda: {
        "session_token": "e2e-token", "risk_profile": "moderate", "preferences": {}
    }
    app.dependency_overrides[get_rate_limiter(max_requests=30)] = lambda: None
    app.dependency_overrides[get_rate_limiter(max_requests=60)] = lambda: None

    yield app, mock_service

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# E2E Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analyze_flow_end_to_end(e2e_app):
    """POST /analyze/AAPL → service.analyze called → 200 with AnalysisResponse shape."""
    app, mock_service = e2e_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/analysis/analyze/AAPL")

    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "AAPL"
    assert data["signal"]["direction"] == "BUY"
    assert "agent_results" in data
    mock_service.analyze.assert_called_once_with("AAPL", {"risk_tolerance": "moderate"})


@pytest.mark.asyncio
async def test_analyze_then_get_history(e2e_app):
    """Analyze a symbol then retrieve its signal history."""
    app, mock_service = e2e_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        post_resp = await client.post("/api/v1/analysis/analyze/AAPL")
        get_resp = await client.get("/api/v1/analysis/history/AAPL")

    assert post_resp.status_code == 200
    assert get_resp.status_code == 200
    history = get_resp.json()
    assert isinstance(history, list)
    assert history[0]["direction"] == "BUY"


@pytest.mark.asyncio
async def test_symbols_endpoint_available_without_session(e2e_app):
    app, _ = e2e_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/analysis/symbols")
    assert resp.status_code == 200
    assert "AAPL" in resp.json()["popular"]
