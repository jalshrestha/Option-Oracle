"""
Shared pytest fixtures for all test layers.
"""
import asyncio
import os

# ---------------------------------------------------------------------------
# CI / test environment stubs — must be set BEFORE any project module import,
# because config/settings.py instantiates Settings() at module level and the
# model_validator requires an API key for the active LLM provider.
# These values are never used for real API calls; all LLM calls are mocked.
# ---------------------------------------------------------------------------
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "sk-test-placeholder-for-ci"
if not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = "test-gemini-placeholder-for-ci"
if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/options_oracle_test"
if not os.environ.get("SUPABASE_URL"):
    os.environ["SUPABASE_URL"] = "https://placeholder.supabase.co"
if not os.environ.get("SUPABASE_SERVICE_KEY"):
    os.environ["SUPABASE_SERVICE_KEY"] = "test-placeholder-key"

from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pandas as pd
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


# ---------------------------------------------------------------------------
# Event loop
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Application client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient against the FastAPI app — no live server needed."""
    from src.api.main import create_app
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Mock orchestrator
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_orchestrator():
    """Returns an AsyncMock that mimics OptionsOracleOrchestrator.analyze_stock()."""
    orchestrator = AsyncMock()
    orchestrator.analyze_stock.return_value = {
        "symbol": "AAPL",
        "signal": {
            "direction": "BUY",
            "strength": "moderate",
            "confidence": 0.72,
            "decision_score": 0.45,
            "strategy_type": "moderate_bullish",
            "market_scenario": "range_bound",
            "reasoning": "Strong bullish technical indicators",
        },
        "agent_results": {
            "technical": {"weighted_score": 0.5, "confidence": 0.8},
            "sentiment": {"aggregate_score": 0.3, "confidence": 0.6},
            "flow": {"flow_score": 0.2, "confidence": 0.5},
            "history": {"pattern_score": 0.4, "confidence": 0.7},
        },
        "strike_recommendations": [],
        "educational_content": "Sample explanation.",
        "confidence": 0.65,
        "market_scenario": "range_bound",
        "agent_weights": {"technical": 0.6, "sentiment": 0.1, "flow": 0.1, "history": 0.2},
    }
    return orchestrator


# ---------------------------------------------------------------------------
# Test data factories
# ---------------------------------------------------------------------------

@pytest.fixture
def signal_factory():
    """Returns a callable that builds valid trading signal dicts."""
    def _build(symbol: str = "AAPL", direction: str = "BUY", confidence: float = 0.7):
        return {
            "symbol": symbol,
            "signal_type": "hybrid",
            "direction": direction,
            "strength": "moderate",
            "confidence_score": confidence,
            "market_scenario": "range_bound",
            "agent_weights": {"technical": 0.6, "sentiment": 0.1, "flow": 0.1, "history": 0.2},
            "technical_analysis": {"weighted_score": 0.45},
            "sentiment_analysis": {"aggregate_score": 0.3},
            "flow_analysis": {"flow_score": 0.2},
            "historical_analysis": {"pattern_score": 0.4},
            "strike_recommendations": [],
            "educational_content": "Test explanation.",
        }
    return _build


@pytest.fixture
def position_factory():
    """Returns a callable that builds valid position dicts."""
    def _build(session_id: str = "test-session-123", symbol: str = "AAPL"):
        return {
            "session_id": session_id,
            "symbol": symbol,
            "option_type": "call",
            "strike_price": 150.0,
            "expiry_date": "2025-12-19",
            "quantity": 1,
            "entry_price": 3.50,
            "current_price": 3.50,
            "status": "open",
            "unrealized_pnl": 0.0,
        }
    return _build


# ---------------------------------------------------------------------------
# OHLCV DataFrame fixture for indicator tests
# ---------------------------------------------------------------------------

@pytest.fixture
def ohlcv_dataframe():
    """60 rows of realistic OHLCV data for technical indicator tests."""
    import numpy as np

    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    base_price = 150.0
    returns = np.random.normal(0.001, 0.015, 60)
    closes = base_price * (1 + returns).cumprod()

    df = pd.DataFrame(
        {
            "Open": closes * (1 + np.random.uniform(-0.005, 0.005, 60)),
            "High": closes * (1 + np.abs(np.random.normal(0, 0.008, 60))),
            "Low": closes * (1 - np.abs(np.random.normal(0, 0.008, 60))),
            "Close": closes,
            "Volume": np.random.randint(5_000_000, 50_000_000, 60),
        },
        index=dates,
    )
    return df


@pytest.fixture
def flat_ohlcv_dataframe():
    """60 rows of flat price OHLCV — for RSI=50, zero ATR, etc."""
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    df = pd.DataFrame(
        {
            "Open": [100.0] * 60,
            "High": [100.0] * 60,
            "Low": [100.0] * 60,
            "Close": [100.0] * 60,
            "Volume": [1_000_000] * 60,
        },
        index=dates,
    )
    return df


@pytest.fixture
def linear_ohlcv_dataframe():
    """60 rows of linearly increasing price — for SMA/MACD tests."""
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    prices = [100.0 + i for i in range(60)]
    df = pd.DataFrame(
        {
            "Open": prices,
            "High": [p + 0.5 for p in prices],
            "Low": [p - 0.5 for p in prices],
            "Close": prices,
            "Volume": [1_000_000] * 60,
        },
        index=dates,
    )
    return df
