"""
Unit tests for src/services/
All repositories and external dependencies are mocked.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.analysis_service import AnalysisService
from src.services.trading_service import TradingService
from src.services.portfolio_service import PortfolioService
from src.schemas.trading import TradeRequest, OptionDetails
from src.exceptions import AnalysisTimeoutError, ExternalAPIError, NotFoundError


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
    def _make_service(self, position_return=None):
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
        return TradingService(position_repo), position_repo

    @pytest.mark.asyncio
    async def test_execute_trade_returns_trade_response(self):
        service, _ = self._make_service()
        req = TradeRequest(symbol="AAPL", action="buy", quantity=1)
        result = await service.execute_trade(req, "session-123")
        assert result.status == "executed"
        assert result.position_id == "pos-abc-123"

    @pytest.mark.asyncio
    async def test_execute_trade_with_option_details(self):
        service, repo = self._make_service()
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

    @pytest.mark.asyncio
    async def test_close_position_returns_position_schema(self):
        service, _ = self._make_service()
        result = await service.close_position("pos-abc-123")
        assert result.status == "closed"
        assert result.id == "pos-abc-123"

    @pytest.mark.asyncio
    async def test_close_position_not_found_raises(self):
        service, repo = self._make_service()
        repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await service.close_position("missing-id")

    @pytest.mark.asyncio
    async def test_refresh_pnl_returns_calculated_value(self):
        service, repo = self._make_service(
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
        pnl = await service.refresh_pnl("p1", current_price=4.00)
        assert pnl == pytest.approx(200.0)
        repo.update_pnl.assert_called_once_with("p1", pytest.approx(200.0))

    @pytest.mark.asyncio
    async def test_refresh_pnl_not_found_raises(self):
        service, repo = self._make_service()
        repo.get_by_id.return_value = None
        with pytest.raises(NotFoundError):
            await service.refresh_pnl("missing", 100.0)


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
