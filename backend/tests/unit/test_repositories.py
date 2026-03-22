"""
Unit tests for src/repositories/
All DB calls are mocked — no live Supabase connection needed.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.repositories.base import BaseRepository
from src.repositories.signals import TradingSignalRepository
from src.repositories.positions import PositionRepository
from src.repositories.sessions import SessionRepository
from src.repositories.stocks import StockRepository
from src.exceptions import DatabaseError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_db(table_result=None, raise_on_execute=False):
    """Build a mock SupabaseManager whose .client.table().*.execute() returns table_result."""
    mock_result = MagicMock()
    mock_result.data = table_result if table_result is not None else []
    mock_result.count = len(table_result) if table_result else 0

    chain = MagicMock()
    chain.select.return_value = chain
    chain.insert.return_value = chain
    chain.upsert.return_value = chain
    chain.update.return_value = chain
    chain.eq.return_value = chain
    chain.gt.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.single.return_value = chain

    if raise_on_execute:
        chain.execute.side_effect = Exception("DB connection refused")
    else:
        chain.execute.return_value = mock_result

    db = MagicMock()
    db.client.table.return_value = chain
    return db


# ---------------------------------------------------------------------------
# BaseRepository
# ---------------------------------------------------------------------------

class TestBaseRepository:
    def test_handle_db_error_raises_database_error(self):
        repo = BaseRepository(_make_db())
        with pytest.raises(DatabaseError):
            repo._handle_db_error(RuntimeError("raw db error"), "test_op")

    def test_handle_db_error_wraps_original(self):
        repo = BaseRepository(_make_db())
        original = ValueError("original cause")
        try:
            repo._handle_db_error(original, "test_op")
        except DatabaseError as exc:
            assert exc.__cause__ is original


# ---------------------------------------------------------------------------
# TradingSignalRepository
# ---------------------------------------------------------------------------

class TestTradingSignalRepository:
    @pytest.mark.asyncio
    async def test_save_returns_id(self):
        db = _make_db(table_result=[{"id": "sig-abc-123"}])
        repo = TradingSignalRepository(db)
        result = await repo.save({"symbol": "AAPL", "direction": "BUY"})
        assert result == "sig-abc-123"

    @pytest.mark.asyncio
    async def test_save_returns_none_when_no_data(self):
        db = _make_db(table_result=[])
        repo = TradingSignalRepository(db)
        result = await repo.save({"symbol": "AAPL"})
        assert result is None

    @pytest.mark.asyncio
    async def test_save_raises_database_error_on_failure(self):
        db = _make_db(raise_on_execute=True)
        repo = TradingSignalRepository(db)
        with pytest.raises(DatabaseError):
            await repo.save({"symbol": "AAPL"})

    @pytest.mark.asyncio
    async def test_get_by_symbol_returns_list(self):
        signals = [{"id": "1", "symbol": "AAPL"}, {"id": "2", "symbol": "AAPL"}]
        db = _make_db(table_result=signals)
        repo = TradingSignalRepository(db)
        result = await repo.get_by_symbol("AAPL")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_latest_returns_first_record(self):
        db = _make_db(table_result=[{"id": "latest-1", "symbol": "TSLA"}])
        repo = TradingSignalRepository(db)
        result = await repo.get_latest("TSLA")
        assert result["id"] == "latest-1"

    @pytest.mark.asyncio
    async def test_get_latest_returns_none_for_unknown_symbol(self):
        db = _make_db(table_result=[])
        repo = TradingSignalRepository(db)
        result = await repo.get_latest("UNKNOWN")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_symbol_raises_on_db_error(self):
        db = _make_db(raise_on_execute=True)
        repo = TradingSignalRepository(db)
        with pytest.raises(DatabaseError):
            await repo.get_by_symbol("AAPL")


# ---------------------------------------------------------------------------
# PositionRepository
# ---------------------------------------------------------------------------

class TestPositionRepository:
    @pytest.mark.asyncio
    async def test_create_returns_id(self):
        db = _make_db(table_result=[{"id": "pos-xyz"}])
        repo = PositionRepository(db)
        result = await repo.create({"symbol": "AAPL", "quantity": 1})
        assert result == "pos-xyz"

    @pytest.mark.asyncio
    async def test_update_pnl_does_not_raise(self):
        db = _make_db(table_result=[])
        repo = PositionRepository(db)
        await repo.update_pnl("pos-xyz", 250.0)  # Should not raise

    @pytest.mark.asyncio
    async def test_update_pnl_raises_on_db_error(self):
        db = _make_db(raise_on_execute=True)
        repo = PositionRepository(db)
        with pytest.raises(DatabaseError):
            await repo.update_pnl("pos-xyz", 100.0)

    @pytest.mark.asyncio
    async def test_get_open_returns_list(self):
        db = _make_db(table_result=[{"id": "p1"}, {"id": "p2"}])
        repo = PositionRepository(db)
        result = await repo.get_open("session-123")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_on_exception(self):
        db = _make_db(raise_on_execute=True)
        repo = PositionRepository(db)
        result = await repo.get_by_id("missing-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_close_returns_updated_record(self):
        db = _make_db(table_result=[{"id": "p1", "status": "closed"}])
        repo = PositionRepository(db)
        result = await repo.close("p1")
        assert result["status"] == "closed"

    @pytest.mark.asyncio
    async def test_close_raises_on_db_error(self):
        db = _make_db(raise_on_execute=True)
        repo = PositionRepository(db)
        with pytest.raises(DatabaseError):
            await repo.close("p1")


# ---------------------------------------------------------------------------
# SessionRepository
# ---------------------------------------------------------------------------

class TestSessionRepository:
    @pytest.mark.asyncio
    async def test_create_returns_session(self):
        db = _make_db(table_result=[{"session_token": "tok-abc"}])
        repo = SessionRepository(db)
        result = await repo.create({"session_token": "tok-abc"})
        assert result["session_token"] == "tok-abc"

    @pytest.mark.asyncio
    async def test_get_returns_none_on_exception(self):
        db = _make_db(raise_on_execute=True)
        repo = SessionRepository(db)
        result = await repo.get("nonexistent-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_touch_does_not_raise(self):
        db = _make_db()
        repo = SessionRepository(db)
        await repo.touch("some-token")  # Should not raise


# ---------------------------------------------------------------------------
# StockRepository
# ---------------------------------------------------------------------------

class TestStockRepository:
    @pytest.mark.asyncio
    async def test_upsert_batch_empty_list_is_noop(self):
        db = _make_db()
        repo = StockRepository(db)
        await repo.upsert_batch([])  # Should not touch DB
        db.client.table.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_batch_calls_upsert(self):
        db = _make_db(table_result=[])
        repo = StockRepository(db)
        await repo.upsert_batch([{"symbol": "AAPL"}, {"symbol": "TSLA"}])
        db.client.table.assert_called()

    @pytest.mark.asyncio
    async def test_get_trending_returns_list(self):
        db = _make_db(table_result=[{"symbol": "NVDA"}, {"symbol": "TSLA"}])
        repo = StockRepository(db)
        result = await repo.get_trending()
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_trending_raises_on_db_error(self):
        db = _make_db(raise_on_execute=True)
        repo = StockRepository(db)
        with pytest.raises(DatabaseError):
            await repo.get_trending()
