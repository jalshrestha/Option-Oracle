import pytest

from src.core.ai_intent_router import AIIntentRouter


def _router_without_clients() -> AIIntentRouter:
    return AIIntentRouter.__new__(AIIntentRouter)


def test_normalize_tool_arguments_uses_selected_stock_context():
    router = _router_without_clients()

    args = router._normalize_tool_arguments(
        "analyze_stock",
        {},
        {
            "user_message": "analyze this",
            "context": {"selectedStock": "tsla"},
        },
    )

    assert args["symbol"] == "TSLA"


@pytest.mark.asyncio
async def test_portfolio_tool_reports_missing_context_instead_of_placeholder():
    router = _router_without_clients()

    result = await router._portfolio_analysis({"analysis_type": "summary"}, {})

    assert result["tool"] == "portfolio_analysis"
    assert result["success"] is False
    assert result["data_quality"]["source_status"] == "unavailable"
    assert "would be here" not in str(result)


@pytest.mark.asyncio
async def test_market_trends_tool_uses_quote_provider(monkeypatch):
    router = _router_without_clients()

    class FakeAlpacaMarketDataClient:
        async def get_current_quote(self, symbol):
            return {
                "symbol": symbol,
                "price": 100.0,
                "change": 2.0 if symbol == "NVDA" else -1.0,
                "change_percent": 2.0 if symbol == "NVDA" else -1.0,
                "volume": 1_000_000,
                "source": "test_quote_provider",
                "timestamp": "2026-01-01T00:00:00",
            }

    import src.data.alpaca_client as alpaca_module

    monkeypatch.setattr(
        alpaca_module,
        "AlpacaMarketDataClient",
        FakeAlpacaMarketDataClient,
    )

    result = await router._get_market_trends({"sector": "tech", "limit": 2})

    assert result["success"] is True
    assert result["data_quality"]["source"] == "alpaca_or_yfinance_quotes"
    assert [row["symbol"] for row in result["trends"]] == ["NVDA", "AAPL"]
    assert "would be here" not in str(result)
