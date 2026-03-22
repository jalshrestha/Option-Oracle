"""
Test data builders — plain functions for constructing test objects
without fixtures when direct calls are more convenient.
"""
from datetime import datetime, timedelta
from typing import Any
import uuid


def make_signal(
    symbol: str = "AAPL",
    direction: str = "BUY",
    confidence: float = 0.70,
    scenario: str = "range_bound",
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "signal_type": "hybrid",
        "direction": direction,
        "strength": "moderate",
        "confidence_score": confidence,
        "market_scenario": scenario,
        "agent_weights": {"technical": 0.6, "sentiment": 0.1, "flow": 0.1, "history": 0.2},
        "technical_analysis": {"weighted_score": 0.45, "confidence": 0.8},
        "sentiment_analysis": {"aggregate_score": 0.3, "confidence": 0.6},
        "flow_analysis": {"flow_score": 0.2, "confidence": 0.5},
        "historical_analysis": {"pattern_score": 0.4, "confidence": 0.7},
        "strike_recommendations": [],
        "educational_content": "Test explanation.",
    }


def make_position(
    session_id: str = "test-session",
    symbol: str = "AAPL",
    option_type: str = "call",
    strike: float = 150.0,
    quantity: int = 1,
) -> dict[str, Any]:
    return {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "symbol": symbol,
        "option_type": option_type,
        "strike_price": strike,
        "expiry_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "quantity": quantity,
        "entry_price": 3.50,
        "current_price": 3.50,
        "status": "open",
        "unrealized_pnl": 0.0,
        "created_at": datetime.now().isoformat(),
    }


def make_session(token: str | None = None) -> dict[str, Any]:
    return {
        "token": token or str(uuid.uuid4()),
        "risk_profile": {
            "risk_tolerance": "moderate",
            "max_position_size": 0.05,
            "account_balance": 100_000,
        },
        "created_at": datetime.now().isoformat(),
        "last_activity": datetime.now().isoformat(),
    }


def make_options_data(symbol: str = "AAPL") -> dict[str, Any]:
    """Minimal options chain dict for flow/risk agent tests."""
    return {
        "symbol": symbol,
        "put_call_ratio": 0.85,
        "total_call_volume": 45_000,
        "total_put_volume": 38_250,
        "total_volume": 83_250,
        "unusual_activity": False,
        "calls": [
            {"strike": 145.0, "expiry": "2025-12-19", "volume": 5000, "oi": 12000, "iv": 0.28},
            {"strike": 150.0, "expiry": "2025-12-19", "volume": 8000, "oi": 20000, "iv": 0.25},
            {"strike": 155.0, "expiry": "2025-12-19", "volume": 3000, "oi": 8000, "iv": 0.30},
        ],
        "puts": [
            {"strike": 145.0, "expiry": "2025-12-19", "volume": 4000, "oi": 10000, "iv": 0.32},
            {"strike": 150.0, "expiry": "2025-12-19", "volume": 6000, "oi": 15000, "iv": 0.29},
            {"strike": 155.0, "expiry": "2025-12-19", "volume": 2500, "oi": 6000, "iv": 0.35},
        ],
    }
