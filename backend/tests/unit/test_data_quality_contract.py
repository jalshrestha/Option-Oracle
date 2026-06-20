import pytest


def test_market_data_fallback_quote_has_no_fake_price():
    from src.data.alpaca_client import AlpacaMarketDataClient

    quote = AlpacaMarketDataClient()._get_fallback_quote("TSLA")

    assert quote["price"] is None
    assert quote["source"] == "unavailable"
    assert quote["data_quality"]["source_status"] == "unavailable"


def test_indicator_fallback_has_no_fake_price_or_rsi():
    from src.indicators.technical_calculator import TechnicalIndicatorsCalculator

    indicators = TechnicalIndicatorsCalculator()._get_fallback_indicators()

    assert indicators["current_price"] is None
    assert indicators["rsi"] is None
    assert indicators["source"] == "unavailable"
    assert indicators["data_quality"]["source_status"] == "unavailable"


def test_orchestrator_blocks_trade_when_technical_data_unavailable():
    from agents.orchestrator import OptionsOracleOrchestrator

    orchestrator = OptionsOracleOrchestrator.__new__(OptionsOracleOrchestrator)
    signal = {
        "direction": "BUY",
        "confidence": 0.75,
        "current_price": 250.0,
    }
    data_quality = {
        "overall": "weak",
        "agents": {
            "technical": {
                "source_status": "unavailable",
                "is_fallback": True,
            }
        },
    }

    decision = orchestrator._build_trade_decision(
        signal=signal,
        strike_recommendations=[
            {"max_loss": 200.0, "max_gain": 500.0}
        ],
        agent_results={},
        data_quality=data_quality,
    )

    assert decision["decision"] == "NO_TRADE"
    assert any("Technical price history is unavailable" in reason for reason in decision["rationale"])


@pytest.mark.asyncio
async def test_risk_agent_returns_no_strikes_without_price():
    from agents.risk_agent import RiskManagementAgent

    agent = RiskManagementAgent(None)
    strikes = await agent.recommend_strikes(
        {"symbol": "TSLA", "direction": "BUY", "confidence": 0.8, "current_price": None},
        {"risk_level": "moderate"},
    )

    assert strikes == []


def test_risk_agent_selects_real_option_contracts_only():
    from datetime import datetime, timedelta

    from agents.risk_agent import RiskManagementAgent

    agent = RiskManagementAgent(None)
    expiration = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    result = agent._select_real_option_candidates(
        options_data={
            "current_price": 100.0,
            "source": "test_real_chain",
            "options_chain": [
                {
                    "strike_price": 102.0,
                    "option_type": "call",
                    "expiration_date": expiration,
                    "bid": 2.1,
                    "ask": 2.3,
                    "last_price": 2.2,
                    "volume": 500,
                    "open_interest": 2500,
                    "implied_volatility": 0.42,
                },
                {
                    "strike_price": 95.0,
                    "option_type": "put",
                    "expiration_date": expiration,
                    "bid": 1.8,
                    "ask": 2.0,
                    "last_price": 1.9,
                    "volume": 400,
                    "open_interest": 2000,
                    "implied_volatility": 0.44,
                },
            ],
        },
        signal={"symbol": "TEST", "direction": "BUY", "confidence": 0.8, "current_price": 100.0},
        user_risk_profile={"risk_level": "moderate", "account_size": 100000, "max_position_percent": 5},
    )

    assert len(result) == 1
    assert result[0]["strike"] == 102.0
    assert result[0]["premium"] == 2.2
    assert result[0]["source"] == "test_real_chain"
    assert result[0]["data_quality"]["is_fallback"] is False
    assert result[0]["probability_profit"] is None


@pytest.mark.asyncio
async def test_technical_agent_returns_unavailable_without_candles(monkeypatch):
    from agents.technical_agent import TechnicalAnalysisAgent

    class FakeMarketDataManager:
        async def get_comprehensive_data(self, symbol):
            return {
                "quote": {"symbol": symbol, "price": 250.0, "change_percent": 1.2, "volume": 123456},
                "technical": {
                    "source": "unavailable",
                    "current_price": None,
                    "data_quality": {
                        "source_status": "unavailable",
                        "source": "historical_price_provider",
                        "confidence_cap": 0.0,
                        "is_fallback": True,
                        "warnings": ["No candles"],
                    },
                },
                "market_conditions": {},
            }

    import src.data.market_data_manager as market_module

    monkeypatch.setattr(market_module, "market_data_manager", FakeMarketDataManager())

    result = await TechnicalAnalysisAgent(None).analyze("TSLA")

    assert result["scenario"] == "DATA_UNAVAILABLE"
    assert result["confidence"] == 0.0
    assert result["market_data_snapshot"]["current_price"] == 250.0
    assert result["data_quality"]["source_status"] == "unavailable"


def test_technical_agent_builds_real_candle_analysis_when_llm_fails():
    from agents.technical_agent import TechnicalAnalysisAgent

    agent = TechnicalAnalysisAgent(None)
    result = agent._build_deterministic_analysis(
        {
            "current_price": 100.0,
            "ma20": 98.0,
            "ma50": 95.0,
            "rsi": 58.0,
            "macd": 1.2,
            "macd_signal": 0.8,
            "bb_position": 0.65,
            "vwap": 99.0,
            "volume_ratio": 1.4,
            "volatility": 32.0,
            "support": 96.0,
            "resistance": 105.0,
        },
        {
            "source_status": "limited",
            "source": "basic_candle_indicators",
            "confidence_cap": 0.55,
            "is_fallback": False,
            "warnings": [],
        },
    )

    assert result["weighted_score"] != 0
    assert result["confidence"] > 0
    assert result["scenario"] in {"range_bound", "strong_uptrend", "strong_downtrend", "high_volatility"}
    assert result["support_resistance"]["support"] == [96.0]


def test_sentiment_agent_builds_real_source_analysis_when_llm_fails():
    from agents.sentiment_agent import SentimentAnalysisAgent

    agent = SentimentAnalysisAgent(None)
    result = agent._build_deterministic_sentiment(
        {
            "news_sentiment": {
                "sentiment_score": 0.4,
                "article_count": 5,
                "source": "yfinance_news",
                "is_fallback": False,
            },
            "stocktwits_sentiment": {
                "sentiment_score": 0.2,
                "message_count": 20,
                "source": "stocktwits_public_stream",
                "is_fallback": False,
            },
            "market_psychology": {
                "vix_level": 18,
                "spy_1m_change_percent": 2.0,
                "source": "yfinance_vix_spy_proxy",
                "is_fallback": False,
            },
        }
    )

    assert result["aggregate_score"] > 0
    assert result["sources"]["news_sentiment"]["article_count"] == 5
    assert "deterministic" in result["risk_factors"][0].lower()


def test_history_agent_builds_real_candle_pattern_without_mock_matches():
    from agents.history_agent import HistoricalPatternAgent

    agent = HistoricalPatternAgent(None)
    result = agent._build_real_pattern_analysis(
        "TSLA",
        {
            "current_price": 100.0,
            "week_return": 2.0,
            "month_return": 4.0,
            "quarter_return": 12.0,
            "ytd_return": 18.0,
            "ma20": 98.0,
            "ma50": 94.0,
            "volatility": 35.0,
            "support": [96.0, 90.0],
            "resistance": [104.0, 110.0],
            "data_points": 252,
            "month_avg": 1.5,
            "day_of_week": "Friday",
            "data_quality": {
                "source_status": "derived",
                "source": "yfinance_history",
                "confidence_cap": 0.65,
                "is_fallback": False,
                "warnings": [],
            },
        },
    )

    validated = agent._validate_pattern_analysis(
        result,
        "TSLA",
        100.0,
        {
            "source_status": "derived",
            "source": "yfinance_history",
            "confidence_cap": 0.65,
            "is_fallback": False,
            "warnings": [],
        },
    )

    assert validated["historical_matches"] == []
    assert validated["data_quality"]["is_fallback"] is False
    assert validated["source"] == "yfinance_history"
    assert validated["confidence"] <= 0.65


def test_history_agent_unavailable_result_has_zero_confidence():
    from agents.history_agent import HistoricalPatternAgent

    result = HistoricalPatternAgent(None)._get_unavailable_history("TSLA", "No candles")

    assert result["confidence"] == 0.0
    assert result["pattern_score"] == 0.0
    assert result["data_quality"]["source_status"] == "unavailable"
    assert result["is_fallback"] is True


def test_flow_agent_limited_chain_data_cannot_claim_unusual_activity():
    from agents.flow_agent import OptionsFlowAgent

    result = OptionsFlowAgent(None)._validate_flow_analysis(
        {
            "flow_score": 0.5,
            "confidence": 0.9,
            "unusual_activity": True,
            "metrics": {
                "put_call_ratio": 0.7,
                "call_volume": 100000,
                "put_volume": 70000,
                "total_volume": 170000,
                "avg_volume_ratio": 0.7,
            },
            "gamma_exposure": {
                "net_gamma": 0.0,
                "gamma_level": "low",
                "dealer_positioning": "neutral",
            },
            "large_trades": [
                {"type": "call", "strike": 100.0, "volume": 10000, "premium": 2.5}
            ],
            "flow_sentiment": "bullish",
            "key_insights": [],
        },
        "TSLA",
        {
            "source_status": "limited",
            "source": "yfinance_real_options",
            "confidence_cap": 0.35,
            "is_fallback": False,
            "warnings": ["Limited options chain detail available"],
        },
    )

    assert result["unusual_activity"] is False
    assert result["large_trades"] == []
    assert result["confidence"] == 0.35


def _sample_analysis_result():
    return {
        "symbol": "AAPL",
        "decision_score": 0.12,
        "market_scenario": "range_bound",
        "signal": {
            "symbol": "AAPL",
            "direction": "HOLD",
            "confidence": 0.12,
            "current_price": 298.01,
        },
        "trade_decision": {
            "decision": "NO_TRADE",
            "direction": "neutral",
            "confidence": 0.12,
            "entry_trigger": "Wait for a clear directional setup.",
            "rationale": [
                "Signal is neutral.",
                "LLM formatter failed; deterministic source scoring used",
                "Signal confidence is below the minimum trade threshold.",
            ],
        },
        "data_quality": {
            "overall": "partial",
            "agents": {
                "technical": {
                    "source_status": "limited",
                    "source": "basic_candle_indicators",
                    "is_fallback": False,
                },
                "flow": {
                    "source_status": "limited",
                    "source": "yfinance_real_options",
                    "is_fallback": False,
                },
                "sentiment": {
                    "source_status": "live",
                    "source": "stocktwits_public_stream",
                    "is_fallback": False,
                },
                "history": {
                    "source_status": "derived",
                    "source": "yfinance_history",
                    "is_fallback": False,
                },
            },
        },
        "agent_results": {
            "technical": {
                "scenario": "range_bound",
                "weighted_score": -0.2,
                "confidence": 0.25,
                "support_resistance": {"support": [287.38], "resistance": [317.4]},
                "volume_analysis": {"relative_volume": 1.63},
                "key_insights": [
                    "Price is below the 20-day moving average.",
                    "Professional indicator library unavailable; using basic candle calculations",
                ],
                "market_data_snapshot": {
                    "current_price": 298.01,
                    "rsi": 39.1,
                    "macd": -1.2,
                    "macd_signal": -0.8,
                    "vwap": 299.3,
                    "ma20": 304.0,
                    "ma50": 296.5,
                },
                "indicators": {
                    "ma": {"signal": -0.2},
                    "rsi": {"signal": -0.1},
                    "macd": {"signal": -0.3},
                },
            },
            "flow": {
                "flow_score": 0.3,
                "confidence": 0.35,
                "unusual_activity": False,
                "metrics": {
                    "put_call_ratio": 0.73,
                    "call_volume": 170000,
                    "put_volume": 124000,
                    "total_volume": 294000,
                },
                "flow_sentiment": "bullish",
                "key_insights": [
                    "Call volume exceeds put volume.",
                    "No sweep/block feed is connected; elevated chain volume is not treated as confirmed unusual activity.",
                ],
            },
            "sentiment": {
                "aggregate_score": 0.4,
                "confidence": 0.55,
                "sentiment_trend": "improving",
                "key_factors": ["News and social sources lean positive."],
                "risk_factors": ["LLM sentiment formatter failed; deterministic source scoring used"],
            },
            "history": {
                "pattern_score": 0.35,
                "confidence": 0.65,
                "dominant_pattern": "reversal",
                "key_levels": {"support": [287.38], "resistance": [317.4]},
                "pattern_insights": [
                    "1-month return 2.0%, 3-month return 8.0%.",
                    "No historical match dates are shown because no real matched-pattern database is connected yet.",
                ],
            },
        },
        "strike_recommendations": [],
    }


def test_agent_evidence_removes_internal_labels():
    from src.core.agent_evidence import build_agent_evidence

    evidence = build_agent_evidence(_sample_analysis_result())
    rendered = str(evidence).lower()

    assert evidence["decision"]["action"] == "NO_TRADE"
    assert evidence["source_coverage"]["technical"] == "daily price and volume candles"
    assert evidence["source_coverage"]["options_flow"] == "public options chain volume/open interest only"
    assert "llm" not in rendered
    assert "formatter" not in rendered
    assert "deterministic" not in rendered
    assert "professional indicator library" not in rendered
    assert "fallback" not in rendered


def test_router_compacts_analysis_to_evidence_packet():
    from src.core.ai_intent_router import AIIntentRouter

    router = AIIntentRouter.__new__(AIIntentRouter)
    compact = router._compact_tool_results_for_prompt([
        {
            "tool": "analyze_stock",
            "success": True,
            "symbol": "AAPL",
            "analysis_result": _sample_analysis_result(),
        }
    ])

    assert compact[0]["tool"] == "analyze_stock"
    assert "evidence" in compact[0]
    assert "agent_results" not in compact[0]
    assert compact[0]["evidence"]["technical"]["indicators"]["rsi"] == 39.1
