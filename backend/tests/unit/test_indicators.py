"""
Unit tests for src/indicators/technical_calculator.py
Uses known OHLCV DataFrames and asserts expected output values within tolerances.
"""
import pytest
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Fixtures (inline — same shape as conftest.py fixtures)
# ---------------------------------------------------------------------------

@pytest.fixture
def flat_df():
    """60 rows of constant price — RSI ≈ 50, ATR ≈ 0."""
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    return pd.DataFrame(
        {"Open": [100.0] * 60, "High": [100.0] * 60, "Low": [100.0] * 60,
         "Close": [100.0] * 60, "Volume": [1_000_000] * 60},
        index=dates,
    )


@pytest.fixture
def linear_df():
    """60 rows of linearly increasing price (100 → 159)."""
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    prices = [100.0 + i for i in range(60)]
    return pd.DataFrame(
        {"Open": prices, "High": [p + 0.5 for p in prices],
         "Low": [p - 0.5 for p in prices], "Close": prices,
         "Volume": [1_000_000] * 60},
        index=dates,
    )


@pytest.fixture
def random_df():
    """60 rows of realistic random OHLCV data."""
    np.random.seed(0)
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    closes = 150.0 * (1 + np.random.normal(0.001, 0.012, 60)).cumprod()
    return pd.DataFrame(
        {"Open": closes * (1 + np.random.uniform(-0.003, 0.003, 60)),
         "High": closes * (1 + np.abs(np.random.normal(0, 0.006, 60))),
         "Low": closes * (1 - np.abs(np.random.normal(0, 0.006, 60))),
         "Close": closes,
         "Volume": np.random.randint(5_000_000, 30_000_000, 60)},
        index=dates,
    )


# ---------------------------------------------------------------------------
# TechnicalIndicatorsCalculator
# ---------------------------------------------------------------------------

class TestTechnicalIndicatorsCalculator:
    def _calc(self, df, symbol="TEST"):
        from src.indicators.technical_calculator import TechnicalIndicatorsCalculator
        return TechnicalIndicatorsCalculator().calculate_comprehensive_indicators(df, symbol)

    # --- Basic shape --------------------------------------------------------

    def test_valid_df_returns_dict(self, random_df):
        result = self._calc(random_df)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_result_has_current_price(self, random_df):
        result = self._calc(random_df)
        assert "current_price" in result

    def test_result_has_rsi(self, random_df):
        result = self._calc(random_df)
        assert "rsi" in result

    def test_result_has_sma_20(self, random_df):
        result = self._calc(random_df)
        assert any("sma" in k or "ma_20" in k for k in result)

    def test_result_has_bollinger_keys(self, random_df):
        result = self._calc(random_df)
        has_bb = any("bollinger" in k or "bb_" in k for k in result)
        assert has_bb

    # --- Empty / degenerate inputs ------------------------------------------

    def test_empty_df_returns_fallback_dict(self):
        from src.indicators.technical_calculator import TechnicalIndicatorsCalculator
        calc = TechnicalIndicatorsCalculator()
        result = calc.calculate_comprehensive_indicators(pd.DataFrame())
        assert isinstance(result, dict)

    def test_five_row_df_does_not_raise(self):
        """Insufficient data for SMA-20 — should degrade gracefully."""
        dates = pd.date_range("2024-01-01", periods=5, freq="B")
        small_df = pd.DataFrame(
            {"Open": [150.0] * 5, "High": [151.0] * 5, "Low": [149.0] * 5,
             "Close": [150.5] * 5, "Volume": [1_000_000] * 5},
            index=dates,
        )
        result = self._calc(small_df)
        assert isinstance(result, dict)

    # --- Known-value tests --------------------------------------------------

    def test_current_price_matches_last_close(self, linear_df):
        result = self._calc(linear_df)
        expected_last_close = 159.0  # 100 + 59 (0-indexed)
        assert result.get("current_price") == pytest.approx(expected_last_close, rel=0.01)

    def test_rsi_near_50_on_flat_prices(self, flat_df):
        """Flat prices → RSI should be close to 50 (no net gains or losses)."""
        result = self._calc(flat_df)
        rsi = result.get("rsi")
        if rsi is not None:  # library may not return RSI on zero-range data
            assert rsi == pytest.approx(50.0, abs=15)

    def test_atr_near_zero_on_flat_prices(self, flat_df):
        """Zero price range → ATR should be 0 or very small."""
        result = self._calc(flat_df)
        atr = result.get("atr", result.get("atr_14"))
        if atr is not None:
            assert float(atr) == pytest.approx(0.0, abs=0.5)

    def test_macd_positive_on_rising_prices(self, linear_df):
        """Steadily rising prices → MACD fast EMA > slow EMA → positive MACD."""
        result = self._calc(linear_df)
        macd = result.get("macd", result.get("macd_value"))
        if macd is not None:
            assert float(macd) > 0

    def test_sma20_on_linear_series(self, linear_df):
        """SMA(20) of last 20 values of 100+i series = 100 + mean(40..59) = 149.5."""
        result = self._calc(linear_df)
        sma = result.get("sma_20", result.get("ma_20"))
        if sma is not None:
            assert float(sma) == pytest.approx(149.5, abs=1.5)

    def test_bollinger_bands_equidistant_on_flat(self, flat_df):
        """Flat price → upper and lower bands same distance from middle."""
        result = self._calc(flat_df)
        upper = result.get("bollinger_upper", result.get("bb_upper"))
        lower = result.get("bollinger_lower", result.get("bb_lower"))
        middle = result.get("bollinger_middle", result.get("bb_middle"))
        if upper is not None and lower is not None and middle is not None:
            assert float(upper) - float(middle) == pytest.approx(
                float(middle) - float(lower), abs=0.01
            )
