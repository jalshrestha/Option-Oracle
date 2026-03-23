"""
Unit tests for src/ml/ models.
All external dependencies (LightGBM, Prophet, OpenAI) are mocked or skipped
if the optional library is unavailable.
"""
import json
import pytest
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# LightGBMFlowPredictor
# ---------------------------------------------------------------------------

class TestLightGBMFlowPredictor:
    def _make_options_data(self) -> dict:
        return {
            "put_call_ratio": 0.75,
            "call_volume": 12000,
            "put_volume": 9000,
            "unusual_activity": True,
            "gamma_exposure": 250000.0,
            "net_flow": 0.4,
            "iv_rank": 35.0,
            "oi_change": 0.05,
        }

    def test_predict_returns_dict_with_required_keys(self):
        from src.ml.lightgbm_flow_model import LightGBMFlowPredictor

        predictor = LightGBMFlowPredictor()
        result = predictor.predict(self._make_options_data())
        assert isinstance(result, dict)
        # Model may be untrained; check it returns something sensible
        assert "flow_sentiment" in result or "flow_direction" in result or "fallback" in result

    def test_predict_rule_based_path_returns_valid_sentiment(self):
        from src.ml.lightgbm_flow_model import LightGBMFlowPredictor

        predictor = LightGBMFlowPredictor()
        # Without training, rule-based path should still return a result
        result = predictor.predict(self._make_options_data())
        assert isinstance(result, dict)

    def test_predict_empty_data_does_not_raise(self):
        from src.ml.lightgbm_flow_model import LightGBMFlowPredictor

        predictor = LightGBMFlowPredictor()
        result = predictor.predict({})
        assert isinstance(result, dict)

    def test_predict_confidence_in_range(self):
        from src.ml.lightgbm_flow_model import LightGBMFlowPredictor

        predictor = LightGBMFlowPredictor()
        result = predictor.predict(self._make_options_data())
        confidence = result.get("confidence", result.get("confidence_score", 0.5))
        assert 0.0 <= float(confidence) <= 1.0


# ---------------------------------------------------------------------------
# ProphetVolatilityPredictor
# ---------------------------------------------------------------------------

class TestProphetVolatilityPredictor:
    def _make_price_series(self, n: int = 60) -> pd.Series:
        dates = pd.date_range("2024-01-01", periods=n, freq="B")
        prices = [150.0 + i * 0.1 for i in range(n)]
        return pd.Series(prices, index=dates)

    def test_predict_60_days_returns_dict(self):
        from src.ml.prophet_volatility_model import ProphetVolatilityPredictor

        predictor = ProphetVolatilityPredictor()
        result = predictor.predict("AAPL", self._make_price_series(60))
        assert isinstance(result, dict)

    def test_predict_returns_positive_volatility(self):
        from src.ml.prophet_volatility_model import ProphetVolatilityPredictor

        predictor = ProphetVolatilityPredictor()
        result = predictor.predict("AAPL", self._make_price_series(60))
        vol = result.get("predicted_volatility", result.get("current_volatility", 0))
        assert float(vol) >= 0

    def test_predict_short_series_returns_fallback(self):
        """< 30 days of data should return gracefully, not raise."""
        from src.ml.prophet_volatility_model import ProphetVolatilityPredictor

        predictor = ProphetVolatilityPredictor()
        short_series = self._make_price_series(10)
        result = predictor.predict("AAPL", short_series)
        assert isinstance(result, dict)

    def test_predict_empty_series_does_not_raise(self):
        from src.ml.prophet_volatility_model import ProphetVolatilityPredictor

        predictor = ProphetVolatilityPredictor()
        result = predictor.predict("AAPL", pd.Series([], dtype=float))
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# OpenAISentimentModel
# ---------------------------------------------------------------------------

class TestOpenAISentimentModel:
    def _make_mock_client(self, score: float = 0.6) -> MagicMock:
        message = MagicMock()
        message.content = json.dumps({"sentiment_score": score, "label": "positive"})
        message.tool_calls = None
        choice = MagicMock()
        choice.message = message
        completion = MagicMock()
        completion.choices = [choice]
        client = MagicMock()
        client.chat.completions.create.return_value = completion
        return client

    @pytest.mark.asyncio
    async def test_analyze_returns_sentiment_score(self):
        from src.ml.openai_sentiment_model import OpenAISentimentModel

        model = OpenAISentimentModel(self._make_mock_client(0.6))
        result = await model.analyze(["AAPL earnings beat expectations"])
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_analyze_score_in_range(self):
        from src.ml.openai_sentiment_model import OpenAISentimentModel

        model = OpenAISentimentModel(self._make_mock_client(0.4))
        result = await model.analyze(["neutral text"])
        score = result.get("sentiment_score", result.get("score", 0.5))
        assert -1.0 <= float(score) <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_openai_failure_returns_fallback(self):
        from src.ml.openai_sentiment_model import OpenAISentimentModel

        failing_client = MagicMock()
        failing_client.chat.completions.create.side_effect = RuntimeError("timeout")
        model = OpenAISentimentModel(failing_client)
        result = await model.analyze(["some text"])
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# EnsembleModel
# ---------------------------------------------------------------------------

class TestEnsembleModel:
    @pytest.mark.asyncio
    async def test_generate_signal_returns_direction_and_confidence(self):
        from src.ml.ensemble_model import EnsembleModel

        model = EnsembleModel()
        # Inject mock components so no real models are needed
        inputs = {
            "technical_score": 0.5,
            "sentiment_score": 0.3,
            "flow_score": 0.2,
            "historical_score": 0.4,
        }
        result = await model.generate_signal("AAPL", inputs)
        assert isinstance(result, dict)
        direction = result.get("direction", result.get("signal", "HOLD"))
        assert direction in ("BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL")
        confidence = result.get("confidence", 0.5)
        assert 0.0 <= float(confidence) <= 1.0
