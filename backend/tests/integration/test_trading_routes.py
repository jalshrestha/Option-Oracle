"""
Integration tests for /api/v1/trading/* routes.
Services are overridden via FastAPI dependency_overrides — no live DB needed.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport

from src.api.dependencies import (
    get_current_session,
    get_portfolio_service,
    get_rate_limiter,
    get_trading_service,
)
from src.schemas.trading import TradeRecommendationResponse, PositionSchema, TradeResponse


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


def _mock_recommendation_response() -> TradeRecommendationResponse:
    return TradeRecommendationResponse(
        id="rec-abc-123",
        symbol="AAPL",
        strategy="long_call",
        action="buy",
        status="draft",
        mode="paper",
        legs=[
            {
                "asset_type": "option",
                "action": "buy",
                "quantity": 1,
                "option_type": "call",
                "strike": 100.0,
                "expiry": "2026-07-18",
                "estimated_price": 2.5,
            }
        ],
        rationale="Rule-based recommendation",
        source="rule_based",
        estimated_cost=250.0,
        max_loss=250.0,
        confidence=0.5,
        risk_score=0.01,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
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
    mock_trading.analyze_buy.return_value = _mock_recommendation_response()
    mock_trading.list_buy_recommendations.return_value = [_mock_recommendation_response()]
    mock_trading.execute_recommendation.return_value = _mock_trade_response()

    from src.schemas.portfolio import PortfolioSummaryResponse, GreeksSchema, RiskMetricsResponse
    mock_portfolio = AsyncMock()
    mock_portfolio.get_open_positions.return_value = [
        {
            "id": "pos-open-123",
            "symbol": "AAPL",
            "quantity": 1,
            "entry_price": 3.5,
            "current_price": 3.5,
            "unrealized_pnl": 0.0,
            "status": "open",
        }
    ]
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
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
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/trading/execute",
            json={"symbol": "AAPL", "action": "short", "quantity": 1},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_close_position_returns_200(trading_app):
    app, mock_trading, _ = trading_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/v1/trading/positions/pos-abc-123/close")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "closed"
    assert data["id"] == "pos-abc-123"


@pytest.mark.asyncio
async def test_close_position_calls_service(trading_app):
    app, mock_trading, _ = trading_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post("/api/v1/trading/positions/pos-xyz/close")
    mock_trading.close_position.assert_called_once_with("pos-xyz", "test-token")


@pytest.mark.asyncio
async def test_get_portfolio_summary_returns_200(trading_app):
    app, _, mock_portfolio = trading_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/trading/portfolio/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_value" in data
    assert data["open_positions"] == 0


@pytest.mark.asyncio
async def test_get_positions_returns_position_list(trading_app):
    app, _, mock_portfolio = trading_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/trading/positions")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["symbol"] == "AAPL"
    mock_portfolio.get_open_positions.assert_called_once_with("test-token")


@pytest.mark.asyncio
async def test_analyze_buy_returns_recommendation(trading_app):
    app, mock_trading, _ = trading_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/trading/analyze-buy",
            json={"symbol": "AAPL", "risk_profile": {"account_balance": 100000}},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "rec-abc-123"
    assert data["symbol"] == "AAPL"
    mock_trading.analyze_buy.assert_called_once()


@pytest.mark.asyncio
async def test_get_buy_recommendations_returns_list(trading_app):
    app, mock_trading, _ = trading_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/trading/buy-recommendations/AAPL")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"
    mock_trading.list_buy_recommendations.assert_called_once_with("AAPL", "test-token")


@pytest.mark.asyncio
async def test_execute_recommendation_calls_service(trading_app):
    app, mock_trading, _ = trading_app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/trading/execute-recommendation",
            json={"recommendation_id": "rec-abc-123", "mode": "paper", "confirmed": True},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "executed"
    mock_trading.execute_recommendation.assert_called_once()
