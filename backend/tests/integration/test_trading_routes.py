"""
Integration tests for /api/v1/trading/* routes.
Services are overridden via FastAPI dependency_overrides — no live DB needed.
"""
import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient

from src.api.dependencies import (
    get_current_session,
    get_portfolio_service,
    get_rate_limiter,
    get_trading_service,
)
from src.schemas.trading import PositionSchema, TradeResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_session():
    return {"session_token": "test-token", "risk_profile": "moderate", "preferences": {}}


def _mock_trade_response() -> TradeResponse:
    import uuid
    return TradeResponse(
        trade_id=str(uuid.uuid4()),
        status="executed",
        position_id="pos-abc-123",
        execution_price=3.50,
        message="Paper trade executed for AAPL",
    )


def _mock_position_schema() -> PositionSchema:
    return PositionSchema(
        id="pos-abc-123",
        symbol="AAPL",
        option_type="call",
        strike_price=155.0,
        expiry_date="2025-12-19",
        quantity=1,
        entry_price=3.50,
        current_price=4.00,
        unrealized_pnl=50.0,
        status="closed",
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def trading_app():
    from src.api.main import app

    mock_trading = AsyncMock()
    mock_trading.execute_trade.return_value = _mock_trade_response()
    mock_trading.close_position.return_value = _mock_position_schema()

    from src.schemas.portfolio import PortfolioSummaryResponse, GreeksSchema, RiskMetricsResponse
    mock_portfolio = AsyncMock()
    mock_portfolio.get_summary.return_value = PortfolioSummaryResponse(
        total_value=50000.0,
        cash_balance=49650.0,
        unrealized_pnl=0.0,
        realized_pnl=0.0,
        open_positions=0,
        total_return_pct=0.0,
        greeks=GreeksSchema(),
        risk_metrics=RiskMetricsResponse(),
        allocation={},
    )

    app.dependency_overrides[get_trading_service] = lambda: mock_trading
    app.dependency_overrides[get_portfolio_service] = lambda: mock_portfolio
    app.dependency_overrides[get_current_session] = lambda: _mock_session()
    app.dependency_overrides[get_rate_limiter(max_requests=20)] = lambda: None
    app.dependency_overrides[get_rate_limiter(max_requests=60)] = lambda: None

    yield app, mock_trading, mock_portfolio

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_execute_trade_returns_200(trading_app):
    app, mock_trading, _ = trading_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/trading/execute",
            json={"symbol": "AAPL", "action": "buy", "quantity": 1},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "executed"
    assert data["position_id"] == "pos-abc-123"


@pytest.mark.asyncio
async def test_execute_trade_calls_service(trading_app):
    app, mock_trading, _ = trading_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/v1/trading/execute",
            json={"symbol": "TSLA", "action": "buy", "quantity": 2},
        )
    mock_trading.execute_trade.assert_called_once()
    call_args = mock_trading.execute_trade.call_args
    assert call_args[0][0].symbol == "TSLA"
    assert call_args[0][1] == "test-token"  # session_token


@pytest.mark.asyncio
async def test_execute_trade_invalid_action_raises_422(trading_app):
    app, _, _ = trading_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/trading/execute",
            json={"symbol": "AAPL", "action": "short", "quantity": 1},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_close_position_returns_200(trading_app):
    app, mock_trading, _ = trading_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post("/api/v1/trading/positions/pos-abc-123/close")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "closed"
    assert data["id"] == "pos-abc-123"


@pytest.mark.asyncio
async def test_close_position_calls_service(trading_app):
    app, mock_trading, _ = trading_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post("/api/v1/trading/positions/pos-xyz/close")
    mock_trading.close_position.assert_called_once_with("pos-xyz")


@pytest.mark.asyncio
async def test_get_portfolio_summary_returns_200(trading_app):
    app, _, mock_portfolio = trading_app
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/api/v1/trading/portfolio/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_value" in data
    assert data["open_positions"] == 0
