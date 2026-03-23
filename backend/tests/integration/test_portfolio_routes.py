"""
Integration tests for /api/v1/portfolio/* routes.
PortfolioService is overridden via FastAPI dependency_overrides — no live DB needed.
"""
import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport

from src.api.dependencies import get_current_session, get_portfolio_service, get_rate_limiter
from src.schemas.portfolio import GreeksSchema, PortfolioSummaryResponse, RiskMetricsResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_session():
    return {"session_token": "test-token", "risk_profile": "moderate", "preferences": {}}


def _mock_summary() -> PortfolioSummaryResponse:
    return PortfolioSummaryResponse(
        total_value=52000.0,
        cash_balance=50000.0,
        unrealized_pnl=2000.0,
        realized_pnl=0.0,
        open_positions=2,
        total_return_pct=4.0,
        greeks=GreeksSchema(delta=1.2, gamma=0.04, theta=-0.5, vega=0.8, rho=0.02),
        risk_metrics=RiskMetricsResponse(var_95=1040.0, max_loss=2000.0),
        allocation={"AAPL": 60.0, "TSLA": 40.0},
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def portfolio_app():
    from src.api.main import app

    mock_service = AsyncMock()
    mock_service.get_summary.return_value = _mock_summary()
    mock_service.get_greeks.return_value = GreeksSchema(
        delta=1.2, gamma=0.04, theta=-0.5, vega=0.8, rho=0.02
    )
    mock_service.get_risk_metrics.return_value = RiskMetricsResponse(
        var_95=1040.0, max_loss=2000.0
    )

    app.dependency_overrides[get_portfolio_service] = lambda: mock_service
    app.dependency_overrides[get_current_session] = lambda: _mock_session()
    app.dependency_overrides[get_rate_limiter(max_requests=60)] = lambda: None

    yield app, mock_service

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_portfolio_summary_returns_200(portfolio_app):
    app, mock_service = portfolio_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/portfolio/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_value"] == 52000.0
    assert data["open_positions"] == 2
    assert data["unrealized_pnl"] == 2000.0


@pytest.mark.asyncio
async def test_get_portfolio_summary_calls_service(portfolio_app):
    app, mock_service = portfolio_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/api/v1/portfolio/summary")
    mock_service.get_summary.assert_called_once_with("test-token")


@pytest.mark.asyncio
async def test_get_greeks_returns_200(portfolio_app):
    app, mock_service = portfolio_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/portfolio/greeks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["delta"] == 1.2
    assert data["gamma"] == pytest.approx(0.04)


@pytest.mark.asyncio
async def test_get_greeks_calls_service(portfolio_app):
    app, mock_service = portfolio_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/api/v1/portfolio/greeks")
    mock_service.get_greeks.assert_called_once_with("test-token")


@pytest.mark.asyncio
async def test_get_risk_metrics_returns_200(portfolio_app):
    app, mock_service = portfolio_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/portfolio/risk")
    assert resp.status_code == 200
    data = resp.json()
    assert data["var_95"] == pytest.approx(1040.0)
    assert data["max_loss"] == pytest.approx(2000.0)


@pytest.mark.asyncio
async def test_get_risk_metrics_calls_service(portfolio_app):
    app, mock_service = portfolio_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/api/v1/portfolio/risk")
    mock_service.get_risk_metrics.assert_called_once_with("test-token")


@pytest.mark.asyncio
async def test_get_portfolio_positions_returns_200(portfolio_app):
    app, _ = portfolio_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/portfolio/positions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["open_positions"] == 2
    assert "AAPL" in data["allocation"]


@pytest.mark.asyncio
async def test_get_performance_stub_returns_200(portfolio_app):
    app, _ = portfolio_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/portfolio/performance")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_alerts_stub_returns_empty_list(portfolio_app):
    app, _ = portfolio_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/portfolio/alerts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_full_portfolio_flow(portfolio_app):
    """Verify summary → greeks → risk all use the same session token."""
    app, mock_service = portfolio_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.get("/api/v1/portfolio/summary")
        await client.get("/api/v1/portfolio/greeks")
        await client.get("/api/v1/portfolio/risk")

    for method in (mock_service.get_summary, mock_service.get_greeks, mock_service.get_risk_metrics):
        args = method.call_args[0]
        assert args[0] == "test-token"
