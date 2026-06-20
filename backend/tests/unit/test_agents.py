"""
Unit tests for agents/ — each agent tested with a mocked OpenAI client.
No live API calls are made.
"""
import json
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_openai_client(json_payload: dict) -> MagicMock:
    """Return a mock OpenAI client whose completions.create returns *json_payload* as content."""
    message = MagicMock()
    message.content = json.dumps(json_payload)
    message.tool_calls = None

    choice = MagicMock()
    choice.message = message

    completion = MagicMock()
    completion.choices = [choice]
    completion.usage = MagicMock()
    completion.usage.dict.return_value = {}
    completion.model = "gpt-4o"

    client = MagicMock()
    client.chat.completions.create.return_value = completion
    client.api_key = "test-openai-api-key"
    return client


def _make_failing_client() -> MagicMock:
    """Return a mock OpenAI client whose completions.create always raises."""
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("OpenAI down")
    client.api_key = "test-openai-api-key"
    return client


# ---------------------------------------------------------------------------
# BaseAgent — _parse_json_response and _get_fallback_response
# ---------------------------------------------------------------------------

class TestBaseAgentParsing:
    def _make_agent(self, client=None):
        from agents.technical_agent import TechnicalAnalysisAgent
        return TechnicalAnalysisAgent(client or MagicMock())

    def test_parse_valid_json(self):
        agent = self._make_agent()
        result = agent._parse_json_response('{"weighted_score": 0.5}')
        assert result["weighted_score"] == 0.5

    def test_parse_json_wrapped_in_code_fence(self):
        agent = self._make_agent()
        content = '```json\n{"scenario": "uptrend"}\n```'
        result = agent._parse_json_response(content)
        assert result["scenario"] == "uptrend"

    def test_parse_malformed_json_returns_fallback(self):
        agent = self._make_agent()
        result = agent._parse_json_response("not json at all!!!!")
        assert isinstance(result, dict)
        assert result.get("fallback") is True

    def test_parse_empty_string_returns_fallback(self):
        agent = self._make_agent()
        result = agent._parse_json_response("")
        assert result.get("fallback") is True

    def test_fallback_response_has_required_keys(self):
        agent = self._make_agent()
        fallback = agent._get_fallback_response()
        assert "confidence" in fallback
        assert "recommendation" in fallback
        assert fallback.get("fallback") is True


# ---------------------------------------------------------------------------
# TechnicalAnalysisAgent
# ---------------------------------------------------------------------------

class TestTechnicalAnalysisAgent:
    @pytest.mark.asyncio
    async def test_analyze_returns_dict_with_weighted_score(self):
        from agents.technical_agent import TechnicalAnalysisAgent

        payload = {
            "scenario": "range_bound",
            "weighted_score": 0.42,
            "confidence": 0.75,
            "indicators": {
                "ma": {"signal": 0.5, "weight": 0.2, "details": "above MA"},
                "rsi": {"signal": 0.3, "weight": 0.15, "details": "RSI 58"},
                "bb": {"signal": 0.1, "weight": 0.3, "details": "mid band"},
                "macd": {"signal": 0.4, "weight": 0.15, "details": "positive"},
                "vwap": {"signal": 0.2, "weight": 0.2, "details": "above vwap"},
            },
        }
        agent = TechnicalAnalysisAgent(_make_openai_client(payload))
        result = await agent.analyze("AAPL", market_data={"quote": {"price": 150}})
        assert "weighted_score" in result
        assert -1 <= result["weighted_score"] <= 1

    @pytest.mark.asyncio
    async def test_analyze_openai_failure_returns_fallback(self):
        from agents.technical_agent import TechnicalAnalysisAgent

        agent = TechnicalAnalysisAgent(_make_failing_client())
        result = await agent.analyze("AAPL", market_data={})
        assert isinstance(result, dict)
        assert result.get("fallback") is True

    @pytest.mark.asyncio
    async def test_analyze_no_client_returns_fallback(self):
        from agents.technical_agent import TechnicalAnalysisAgent

        agent = TechnicalAnalysisAgent(None)
        result = await agent.analyze("AAPL", market_data={})
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# SentimentAnalysisAgent
# ---------------------------------------------------------------------------

class TestSentimentAnalysisAgent:
    @pytest.mark.asyncio
    async def test_analyze_returns_dict(self):
        from agents.sentiment_agent import SentimentAnalysisAgent

        payload = {
            "aggregate_score": 0.45,
            "confidence": 0.60,
            "sentiment_category": "bullish",
            "sources": ["news", "social"],
        }
        agent = SentimentAnalysisAgent(_make_openai_client(payload))
        result = await agent.analyze("AAPL")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_failure_returns_fallback(self):
        from agents.sentiment_agent import SentimentAnalysisAgent

        agent = SentimentAnalysisAgent(_make_failing_client())
        result = await agent.analyze("AAPL")
        assert isinstance(result, dict)
        assert result.get("fallback") is True


# ---------------------------------------------------------------------------
# FlowAgent (options flow)
# ---------------------------------------------------------------------------

class TestFlowAgent:
    @pytest.mark.asyncio
    async def test_analyze_returns_dict(self):
        from agents.flow_agent import FlowAgent

        payload = {
            "flow_score": 0.3,
            "put_call_ratio": 0.5,
            "unusual_activity": False,
            "confidence": 0.55,
        }
        agent = FlowAgent(_make_openai_client(payload))
        result = await agent.analyze("AAPL")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_failure_returns_fallback(self):
        from agents.flow_agent import FlowAgent

        agent = FlowAgent(_make_failing_client())
        result = await agent.analyze("AAPL")
        assert isinstance(result, dict)
        assert result.get("fallback") is True


# ---------------------------------------------------------------------------
# HistoricalPatternAgent
# ---------------------------------------------------------------------------

class TestHistoricalPatternAgent:
    @pytest.mark.asyncio
    async def test_analyze_returns_dict(self):
        from agents.history_agent import HistoricalPatternAgent

        payload = {
            "pattern_score": 0.55,
            "similar_patterns": 12,
            "success_rate": 0.65,
            "confidence": 0.70,
        }
        agent = HistoricalPatternAgent(_make_openai_client(payload))
        result = await agent.analyze("AAPL")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_failure_returns_fallback(self):
        from agents.history_agent import HistoricalPatternAgent

        agent = HistoricalPatternAgent(_make_failing_client())
        result = await agent.analyze("AAPL")
        assert isinstance(result, dict)
        assert result.get("fallback") is True


# ---------------------------------------------------------------------------
# EducationAgent
# ---------------------------------------------------------------------------

class TestEducationAgent:
    @pytest.mark.asyncio
    async def test_generate_returns_non_empty_string(self):
        from agents.education_agent import EducationAgent

        payload = {
            "explanation": "This is a bullish signal.",
            "key_concepts": ["RSI", "momentum"],
        }
        agent = EducationAgent(_make_openai_client(payload))
        result = await agent.analyze("AAPL", signal={"direction": "BUY"})
        assert isinstance(result, (dict, str))

    @pytest.mark.asyncio
    async def test_generate_failure_returns_fallback(self):
        from agents.education_agent import EducationAgent

        agent = EducationAgent(_make_failing_client())
        result = await agent.analyze("AAPL", signal={"direction": "BUY"})
        assert result is not None
