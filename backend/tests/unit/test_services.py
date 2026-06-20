"""
Unit tests for src/services/
All repositories and external dependencies are mocked.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.analysis_service import AnalysisService
from src.services.trading_service import TradingService
from src.services.portfolio_service import PortfolioService
from src.schemas.trading import AnalyzeBuyRequest, ExecuteRecommendationRequest, TradeRequest, OptionDetails
from src.exceptions import AnalysisTimeoutError, ExternalAPIError, NotFoundError, ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_raw_analysis(symbol: str = "AAPL") -> dict:
    return {
        "symbol": symbol,
        "signal": {
            "direction": "BUY",
            "strength": "moderate",
            "confidence": 0.72,
            "decision_score": 0.45,
            "strategy_type": "moderate_bullish",
            "market_scenario": "range_bound",
            "reasoning": "Positive technical indicators",
        },
        "agent_results": {"technical": {"weighted_score": 0.5}},
        "strike_recommendations": [],
        "educational_content": "Test explanation.",
        "confidence": 0.72,
        "market_scenario": "range_bound",
        "agent_weights": {"technical": 0.6},
        "analysis_time_seconds": 5.2,
    }


# ---------------------------------------------------------------------------
# AnalysisService
# ---------------------------------------------------------------------------

class TestAnalysisService:
    def _make_service(self, raw_return=None, orchestrator_raises=None):
        orchestrator = AsyncMock()
        if orchestrator_raises:
            orchestrator.analyze_stock.side_effect = orchestrator_raises
        else:
            orchestrator.analyze_stock.return_value = raw_return or _make_raw_analysis()
        signal_repo = AsyncMock()
        signal_repo.save.return_value = "sig-123"
        signal_repo.get_by_symbol.return_value = []
        return AnalysisService(orchestrator, signal_repo), orchestrator, signal_repo

    @pytest.mark.asyncio
    async def test_analyze_returns_analysis_response(self):
        service, _, _ = self._make_service()
        result = await service.analyze("AAPL", {"risk_tolerance": "moderate"})
        assert result.symbol == "AAPL"
        assert result.signal.direction == "BUY"
        assert 0 <= result.confidence <= 1

    @pytest.mark.asyncio
    async def test_analyze_calls_orchestrator(self):
        service, orchestrator, _ = self._make_service()
        await service.analyze("TSLA", {})
        orchestrator.analyze_stock.assert_called_once_with("TSLA", {})

    @pytest.mark.asyncio
    async def test_analyze_saves_signal(self):
        service, _, signal_repo = self._make_service()
        await service.analyze("AAPL", {})
        signal_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_timeout_raises_analysis_timeout_error(self):
        import asyncio
        service, orchestrator, _ = self._make_service()

        async def slow():
            await asyncio.sleep(999)

        orchestrator.analyze_stock.side_effect = asyncio.TimeoutError()
        with pytest.raises(AnalysisTimeoutError):
            await service.analyze("AAPL", {})

    @pytest.mark.asyncio
    async def test_analyze_orchestrator_exception_raises_external_api_error(self):
        service, _, _ = self._make_service(orchestrator_raises=RuntimeError("OpenAI down"))
        with pytest.raises(ExternalAPIError):
            await service.analyze("AAPL", {})

    @pytest.mark.asyncio
    async def test_db_failure_does_not_propagate(self):
        service, _, signal_repo = self._make_service()
        signal_repo.save.side_effect = Exception("DB unavailable")
        # Should still return response despite save failure
        result = await service.analyze("AAPL", {})
        assert result.symbol == "AAPL"

    @pytest.mark.asyncio
    async def test_get_history_returns_signal_list(self):
        service, _, signal_repo = self._make_service()
        signal_repo.get_by_symbol.return_value = [
            {
                "direction": "BUY",
                "strength": "moderate",
                "confidence_score": 0.7,
                "market_scenario": "range_bound",
            }
        ]
        result = await service.get_history("AAPL")
        assert len(result) == 1
        assert result[0].direction == "BUY"

    @pytest.mark.asyncio
    async def test_get_history_empty_returns_empty_list(self):
        service, _, signal_repo = self._make_service()
        signal_repo.get_by_symbol.return_value = []
        result = await service.get_history("AAPL")
        assert result == []


# ---------------------------------------------------------------------------
# TradingService
# ---------------------------------------------------------------------------

class TestTradingService:
    def _make_service(self, position_return=None, recommendation_return=None):
        position_repo = AsyncMock()
        position_repo.create.return_value = "pos-abc-123"
        position_repo.get_by_id.return_value = position_return or {
            "id": "pos-abc-123",
            "symbol": "AAPL",
            "quantity": 1,
            "entry_price": 3.50,
            "current_price": 3.50,
            "unrealized_pnl": 0.0,
            "status": "open",
        }
        position_repo.close.return_value = {
            "id": "pos-abc-123",
            "symbol": "AAPL",
            "quantity": 1,
            "entry_price": 3.50,
            "current_price": 4.00,
            "unrealized_pnl": 50.0,
            "status": "closed",
        }
        position_repo.update_pnl.return_value = None
        recommendation_repo = AsyncMock()
        recommendation_repo.create.return_value = recommendation_return or self._recommendation_record()
        recommendation_repo.list_for_symbol.return_value = [recommendation_return or self._recommendation_record()]
        recommendation_repo.get_by_id.return_value = recommendation_return or self._recommendation_record()
        recommendation_repo.mark_executed.return_value = {
            **(recommendation_return or self._recommendation_record()),
            "status": "executed",
            "executed_position_id": "pos-abc-123",
        }
        return TradingService(position_repo, recommendation_repo), position_repo, recommendation_repo

    @staticmethod
    def _recommendation_record(**overrides):
        record = {
            "id": "rec-abc-123",
            "symbol": "AAPL",
            "strategy": "long_call",
            "action": "buy",
            "status": "draft",
            "mode": "paper",
            "legs": [
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
            "rationale": "Rule-based recommendation",
            "source": "rule_based",
            "source_analysis_id": None,
            "estimated_cost": 250.0,
            "max_loss": 250.0,
            "confidence": 0.5,
            "risk_score": 0.01,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=30),
            "executed_position_id": None,
            "created_at": datetime.now(timezone.utc),
        }
        record.update(overrides)
        return record

    @pytest.mark.asyncio
    async def test_execute_trade_returns_trade_response(self):
        service, _, _ = self._make_service()
        req = TradeRequest(symbol="AAPL", action="buy", quantity=1)
        result = await service.execute_trade(req, "session-123")
        assert result.status == "executed"
        assert result.position_id == "pos-abc-123"

    @pytest.mark.asyncio
    async def test_execute_trade_with_option_details(self):
        service, repo, _ = self._make_service()
        req = TradeRequest(
            symbol="AAPL",
            action="buy",
            quantity=1,
            option_details=OptionDetails(option_type="call", strike=155.0, expiry="2025-12-19"),
        )
        await service.execute_trade(req, "session-123")
        call_args = repo.create.call_args[0][0]
        assert call_args["option_type"] == "call"
        assert call_args["strike_price"] == 155.0
        assert "created_at" not in call_args

    @pytest.mark.asyncio
    async def test_close_position_returns_position_schema(self):
        service, _, _ = self._make_service()
        result = await service.close_position("pos-abc-123", "session-123")
        assert result.status == "closed"
        assert result.id == "pos-abc-123"

    @pytest.mark.asyncio
    async def test_close_position_not_found_raises(self):
        service, repo, _ = self._make_service()
        repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await service.close_position("missing-id", "session-123")

    @pytest.mark.asyncio
    async def test_close_position_filters_by_session(self):
        service, repo, _ = self._make_service()
        await service.close_position("pos-abc-123", "session-123")
        repo.get_by_id.assert_called_once_with("pos-abc-123", session_id="session-123")
        repo.close.assert_called_once_with("pos-abc-123", session_id="session-123")

    @pytest.mark.asyncio
    async def test_refresh_pnl_returns_calculated_value(self):
        service, repo, _ = self._make_service(
            position_return={
                "id": "p1",
                "symbol": "AAPL",
                "entry_price": 3.00,
                "quantity": 2,
                "option_type": "call",
                "current_price": 3.00,
                "unrealized_pnl": 0.0,
                "status": "open",
            }
        )
        # current 4.00 - entry 3.00 = 1.00 * qty 2 * multiplier 100 = 200.0
        pnl = await service.refresh_pnl("p1", "session-123", current_price=4.00)
        assert pnl == pytest.approx(200.0)
        repo.update_pnl.assert_called_once_with(
            "p1", pytest.approx(200.0), session_id="session-123"
        )

    @pytest.mark.asyncio
    async def test_analyze_buy_persists_recommendation(self):
        service, _, rec_repo = self._make_service()
        result = await service.analyze_buy(
            AnalyzeBuyRequest(symbol="aapl", risk_profile={"account_balance": 100000}),
            "session-123",
        )
        assert result.symbol == "AAPL"
        assert result.status == "draft"
        rec_repo.create.assert_called_once()
        saved = rec_repo.create.call_args[0][0]
        assert saved["session_id"] == "session-123"
        assert saved["symbol"] == "AAPL"

    @pytest.mark.asyncio
    async def test_list_buy_recommendations_filters_by_session(self):
        service, _, rec_repo = self._make_service()
        result = await service.list_buy_recommendations("AAPL", "session-123")
        assert len(result) == 1
        rec_repo.list_for_symbol.assert_called_once_with("session-123", "AAPL")

    @pytest.mark.asyncio
    async def test_execute_recommendation_requires_confirmation(self):
        service, _, _ = self._make_service()
        with pytest.raises(ValidationError):
            await service.execute_recommendation(
                ExecuteRecommendationRequest(recommendation_id="rec-abc-123", confirmed=False),
                "session-123",
            )

    @pytest.mark.asyncio
    async def test_execute_recommendation_live_mode_fails_closed(self):
        service, _, _ = self._make_service()
        with pytest.raises(ValidationError):
            await service.execute_recommendation(
                ExecuteRecommendationRequest(
                    recommendation_id="rec-abc-123",
                    mode="live",
                    confirmed=True,
                ),
                "session-123",
            )

    @pytest.mark.asyncio
    async def test_execute_recommendation_rejects_expired(self):
        service, _, _ = self._make_service(
            recommendation_return=self._recommendation_record(
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)
            )
        )
        with pytest.raises(ValidationError):
            await service.execute_recommendation(
                ExecuteRecommendationRequest(recommendation_id="rec-abc-123", confirmed=True),
                "session-123",
            )

    @pytest.mark.asyncio
    async def test_execute_recommendation_creates_position_and_marks_executed(self):
        service, position_repo, rec_repo = self._make_service()
        result = await service.execute_recommendation(
            ExecuteRecommendationRequest(recommendation_id="rec-abc-123", confirmed=True),
            "session-123",
        )
        assert result.status == "executed"
        position_repo.create.assert_called_once()
        rec_repo.mark_executed.assert_called_once_with(
            "rec-abc-123", "session-123", "pos-abc-123"
        )

    @pytest.mark.asyncio
    async def test_refresh_pnl_not_found_raises(self):
        service, repo, _ = self._make_service()
        repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await service.refresh_pnl("missing", "session-123", 100.0)


# ---------------------------------------------------------------------------
# PortfolioService
# ---------------------------------------------------------------------------

class TestPortfolioService:
    def _make_service(self, positions=None):
        repo = AsyncMock()
        repo.get_open.return_value = positions or []
        return PortfolioService(repo)

    @pytest.mark.asyncio
    async def test_get_summary_empty_portfolio(self):
        service = self._make_service()
        result = await service.get_summary("session-123")
        assert result.open_positions == 0
        assert result.unrealized_pnl == 0.0

    @pytest.mark.asyncio
    async def test_get_summary_with_positions(self):
        positions = [
            {"symbol": "AAPL", "entry_price": 3.50, "quantity": 1,
             "option_type": "call", "unrealized_pnl": 50.0, "greeks": {}},
        ]
        service = self._make_service(positions=positions)
        result = await service.get_summary("session-123")
        assert result.open_positions == 1
        assert result.unrealized_pnl == 50.0

    @pytest.mark.asyncio
    async def test_get_greeks_empty_returns_zero_greeks(self):
        service = self._make_service()
        greeks = await service.get_greeks("session-123")
        assert greeks.delta == 0.0
        assert greeks.gamma == 0.0

    @pytest.mark.asyncio
    async def test_get_greeks_aggregates_across_positions(self):
        positions = [
            {"option_type": "call", "quantity": 2, "greeks": {"delta": 0.5, "gamma": 0.02}},
            {"option_type": "put", "quantity": 1, "greeks": {"delta": -0.4, "gamma": 0.01}},
        ]
        service = self._make_service(positions=positions)
        greeks = await service.get_greeks("s")
        assert greeks.delta == pytest.approx(0.5 * 2 + (-0.4) * 1)
        assert greeks.gamma == pytest.approx(0.02 * 2 + 0.01 * 1)

    def test_aggregate_greeks_ignores_stock_positions(self):
        positions = [
            {"symbol": "AAPL", "quantity": 100, "entry_price": 150.0},  # no option_type
        ]
        greeks = PortfolioService._aggregate_greeks(positions)
        assert greeks.delta == 0.0

    def test_calculate_risk_empty_returns_defaults(self):
        risk = PortfolioService._calculate_risk([], 0.0)
        assert risk.var_95 == 0.0
        assert risk.max_loss == 0.0

    def test_calculate_allocation_by_symbol(self):
        positions = [
            {"symbol": "AAPL", "entry_price": 100.0, "quantity": 1},
            {"symbol": "TSLA", "entry_price": 100.0, "quantity": 1},
        ]
        alloc = PortfolioService._calculate_allocation(positions, 200.0)
        assert alloc["AAPL"] == pytest.approx(50.0)
        assert alloc["TSLA"] == pytest.approx(50.0)
