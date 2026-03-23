"""
Unit tests for src/schemas/
Tests valid inputs, invalid inputs, coercions, and validators for every schema.
"""
import pytest
from pydantic import ValidationError

from src.schemas.analysis import AnalysisRequest, SignalSchema, AnalysisResponse
from src.schemas.trading import TradeRequest, OptionDetails
from src.schemas.portfolio import GreeksSchema, PortfolioSummaryResponse, RiskMetricsResponse
from src.schemas.common import ErrorResponse, PaginationParams


# ---------------------------------------------------------------------------
# AnalysisRequest
# ---------------------------------------------------------------------------

class TestAnalysisRequest:
    def test_lowercase_coerced_to_uppercase(self):
        req = AnalysisRequest(symbol="aapl")
        assert req.symbol == "AAPL"

    def test_mixed_case_coerced(self):
        req = AnalysisRequest(symbol="Tsla")
        assert req.symbol == "TSLA"

    def test_symbol_too_long_raises(self):
        with pytest.raises(ValidationError, match="1.5 characters"):
            AnalysisRequest(symbol="TOOLONG")

    def test_empty_symbol_raises(self):
        with pytest.raises(ValidationError):
            AnalysisRequest(symbol="")

    def test_symbol_with_digits_raises(self):
        with pytest.raises(ValidationError, match="letters"):
            AnalysisRequest(symbol="A1PL")

    def test_symbol_with_space_raises(self):
        with pytest.raises(ValidationError):
            AnalysisRequest(symbol="A PL")

    def test_single_char_symbol_valid(self):
        req = AnalysisRequest(symbol="F")
        assert req.symbol == "F"

    def test_five_char_symbol_valid(self):
        req = AnalysisRequest(symbol="GOOGL")
        assert req.symbol == "GOOGL"

    def test_whitespace_stripped_before_validation(self):
        req = AnalysisRequest(symbol=" AAPL ")
        assert req.symbol == "AAPL"


# ---------------------------------------------------------------------------
# SignalSchema
# ---------------------------------------------------------------------------

class TestSignalSchema:
    def test_valid_buy_signal(self):
        s = SignalSchema(
            direction="BUY",
            strength="moderate",
            confidence=0.72,
            decision_score=0.45,
            strategy_type="moderate_bullish",
            market_scenario="range_bound",
            reasoning="Technical indicators positive",
        )
        assert s.direction == "BUY"
        assert 0 <= s.confidence <= 1

    def test_invalid_direction_raises(self):
        with pytest.raises(ValidationError):
            SignalSchema(
                direction="MAYBE",
                strength="moderate",
                confidence=0.5,
                decision_score=0.2,
                strategy_type="neutral",
                market_scenario="range_bound",
                reasoning="",
            )

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            SignalSchema(
                direction="BUY",
                strength="strong",
                confidence=1.5,  # > 1.0
                decision_score=0.8,
                strategy_type="aggressive_bullish",
                market_scenario="uptrend",
                reasoning="",
            )

    def test_decision_score_out_of_range_raises(self):
        with pytest.raises(ValidationError):
            SignalSchema(
                direction="SELL",
                strength="weak",
                confidence=0.3,
                decision_score=-2.0,  # < -1.0
                strategy_type="neutral",
                market_scenario="range_bound",
                reasoning="",
            )


# ---------------------------------------------------------------------------
# TradeRequest
# ---------------------------------------------------------------------------

class TestTradeRequest:
    def test_valid_market_buy(self):
        req = TradeRequest(symbol="AAPL", action="buy", quantity=2)
        assert req.symbol == "AAPL"
        assert req.order_type == "market"

    def test_symbol_uppercased(self):
        req = TradeRequest(symbol="tsla", action="sell", quantity=1)
        assert req.symbol == "TSLA"

    def test_zero_quantity_raises(self):
        with pytest.raises(ValidationError):
            TradeRequest(symbol="AAPL", action="buy", quantity=0)

    def test_negative_quantity_raises(self):
        with pytest.raises(ValidationError):
            TradeRequest(symbol="AAPL", action="buy", quantity=-5)

    def test_limit_order_without_price_raises(self):
        with pytest.raises(ValidationError, match="limit_price"):
            TradeRequest(symbol="AAPL", action="buy", quantity=1, order_type="limit")

    def test_limit_order_with_price_valid(self):
        req = TradeRequest(
            symbol="AAPL", action="buy", quantity=1, order_type="limit", limit_price=150.0
        )
        assert req.limit_price == 150.0

    def test_with_option_details(self):
        req = TradeRequest(
            symbol="AAPL",
            action="buy",
            quantity=1,
            option_details=OptionDetails(option_type="call", strike=155.0, expiry="2025-12-19"),
        )
        assert req.option_details.option_type == "call"
        assert req.option_details.strike == 155.0

    def test_invalid_option_type_raises(self):
        with pytest.raises(ValidationError):
            OptionDetails(option_type="straddle", strike=150.0, expiry="2025-12-19")

    def test_zero_strike_raises(self):
        with pytest.raises(ValidationError):
            OptionDetails(option_type="put", strike=0, expiry="2025-12-19")


# ---------------------------------------------------------------------------
# PortfolioSummaryResponse
# ---------------------------------------------------------------------------

class TestPortfolioSummaryResponse:
    def test_valid_summary(self):
        summary = PortfolioSummaryResponse(
            total_value=105_000.0,
            cash_balance=95_000.0,
            unrealized_pnl=5_000.0,
            realized_pnl=0.0,
            open_positions=2,
            total_return_pct=5.0,
            greeks=GreeksSchema(delta=0.5, gamma=0.02),
            risk_metrics=RiskMetricsResponse(var_95=2_500.0),
        )
        assert summary.total_value == 105_000.0
        assert summary.greeks.delta == 0.5


# ---------------------------------------------------------------------------
# PaginationParams
# ---------------------------------------------------------------------------

class TestPaginationParams:
    def test_defaults(self):
        p = PaginationParams()
        assert p.page == 1
        assert p.page_size == 20

    def test_max_page_size_enforced(self):
        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)

    def test_zero_page_raises(self):
        with pytest.raises(ValidationError):
            PaginationParams(page=0)


# ---------------------------------------------------------------------------
# ErrorResponse
# ---------------------------------------------------------------------------

class TestErrorResponse:
    def test_valid_error_response(self):
        err = ErrorResponse(
            error="Not found",
            code="NOT_FOUND",
            request_id="abc-123",
            timestamp="2025-01-01T00:00:00",
        )
        assert err.code == "NOT_FOUND"
        assert err.request_id == "abc-123"
