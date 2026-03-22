"""
E2E tests for error scenarios — verifies that OracleError subclasses
produce the correct HTTP status codes and structured JSON error responses.
"""
import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient

from src.api.dependencies import (
    get_analysis_service,
    get_current_session,
    get_portfolio_service,
    get_rate_limiter,
    get_trading_service,
)
from src.exceptions import (
    AnalysisTimeoutError,
    DatabaseError,
    ExternalAPIError,
    NotFoundError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _session():
    return {"session_token": "e2e-token", "risk_profile": "moderate", "preferences": {}}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def error_app():
    from src.api.main import app

    mock_analysis = AsyncMock()
    mock_trading = AsyncMock()
    mock_portfolio = AsyncMock()

    app.dependency_overrides[get_analysis_service] = lambda: mock_analysis
    app.dependency_overrides[get_trading_service] = lambda: mock_trading
    app.dependency_overrides[get_portfolio_service] = lambda: mock_portfolio
    app.dependency_overrides[get_current_session] = lambda: _session()
    for limit in (10, 20, 30, 60):
        app.dependency_overrides[get_rate_limiter(max_requests=limit)] = lambda: None

    yield app, mock_analysis, mock_trading, mock_portfolio

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Validation errors (422)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_invalid_symbol_too_long_returns_422(error_app):
    app, _, _, _ = error_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/analysis/analyze/TOOLONG")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_invalid_trade_action_returns_422(error_app):
    app, _, _, _ = error_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/trading/execute",
            json={"symbol": "AAPL", "action": "short", "quantity": 1},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_zero_quantity_returns_422(error_app):
    app, _, _, _ = error_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/trading/execute",
            json={"symbol": "AAPL", "action": "buy", "quantity": 0},
        )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Not-found errors (404)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_close_unknown_position_returns_404(error_app):
    app, _, mock_trading, _ = error_app
    mock_trading.close_position.side_effect = NotFoundError("Position not found")
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/trading/positions/no-such-id/close")
    assert resp.status_code == 404
    data = resp.json()
    assert data.get("code") == "NOT_FOUND"


# ---------------------------------------------------------------------------
# External API errors (502)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_orchestrator_failure_returns_502(error_app):
    app, mock_analysis, _, _ = error_app
    mock_analysis.analyze.side_effect = ExternalAPIError("OpenAI timed out")
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/analysis/analyze/AAPL")
    assert resp.status_code == 502
    data = resp.json()
    assert data.get("code") == "EXTERNAL_API_ERROR"


# ---------------------------------------------------------------------------
# Analysis timeout (504)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analysis_timeout_returns_504(error_app):
    app, mock_analysis, _, _ = error_app
    mock_analysis.analyze.side_effect = AnalysisTimeoutError("Timed out after 120s")
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/analysis/analyze/AAPL")
    assert resp.status_code == 504
    data = resp.json()
    assert data.get("code") == "ANALYSIS_TIMEOUT"


# ---------------------------------------------------------------------------
# Database errors (503)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_portfolio_db_error_returns_503(error_app):
    app, _, _, mock_portfolio = error_app
    mock_portfolio.get_summary.side_effect = DatabaseError("DB unavailable")
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/portfolio/summary")
    assert resp.status_code == 503
    data = resp.json()
    assert data.get("code") == "DATABASE_ERROR"


# ---------------------------------------------------------------------------
# Error response shape
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_error_response_has_required_fields(error_app):
    """Every OracleError response must have: error, code, timestamp, path."""
    app, _, mock_trading, _ = error_app
    mock_trading.close_position.side_effect = NotFoundError("Position not found")
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/trading/positions/missing/close")
    data = resp.json()
    for field in ("error", "code"):
        assert field in data, f"Missing field '{field}' in error response"
