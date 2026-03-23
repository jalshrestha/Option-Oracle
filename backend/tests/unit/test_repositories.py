"""
Unit tests for src/repositories/
All DB calls use a mocked AsyncSession — no live DB connection needed.
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.repositories.base import BaseRepository
from src.repositories.signals import TradingSignalRepository
from src.repositories.positions import PositionRepository
from src.repositories.sessions import SessionRepository
from src.repositories.stocks import StockRepository
from src.exceptions import DatabaseError, NotFoundError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_session():
    """Return an AsyncMock that looks like an AsyncSession."""
    session = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


def _scalar_result(value):
    """Build a mock execute() result whose .scalars().all() returns value."""
    result = MagicMock()
    result.scalars.return_value.all.return_value = value
    result.scalar_one_or_none.return_value = value[0] if value else None
    return result


# ---------------------------------------------------------------------------
# BaseRepository
# ---------------------------------------------------------------------------

class TestBaseRepository:
    def test_handle_db_error_raises_database_error(self):
        repo = BaseRepository(_mock_session())
        with pytest.raises(DatabaseError):
            repo._handle_db_error(RuntimeError("raw db error"), "test_op")

    def test_handle_db_error_wraps_original(self):
        repo = BaseRepository(_mock_session())
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
        session = _mock_session()
        repo = TradingSignalRepository(session)

        # Mock TradingSignal model construction + flush sets .id
        fake_id = uuid.uuid4()
        with patch("src.repositories.signals.TradingSignal") as MockSignal:
            instance = MagicMock()
            instance.id = fake_id
            MockSignal.return_value = instance
            result = await repo.save({"symbol": "AAPL", "direction": "BUY"})

        assert result == str(fake_id)
        session.add.assert_called_once_with(instance)
        session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_raises_database_error_on_failure(self):
        session = _mock_session()
        session.flush.side_effect = Exception("DB error")
        repo = TradingSignalRepository(session)

        with patch("src.repositories.signals.TradingSignal"):
            with pytest.raises(DatabaseError):
                await repo.save({"symbol": "AAPL"})

    @pytest.mark.asyncio
    async def test_get_by_symbol_returns_list(self):
        session = _mock_session()
        fake_rows = [MagicMock(), MagicMock()]
        for row in fake_rows:
            row.__table__ = MagicMock()
            row.__table__.columns = []
        session.execute.return_value = _scalar_result(fake_rows)
        repo = TradingSignalRepository(session)

        with patch("src.repositories.signals.select"):
            result = await repo.get_by_symbol("AAPL")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_symbol_raises_on_db_error(self):
        session = _mock_session()
        session.execute.side_effect = Exception("DB error")
        repo = TradingSignalRepository(session)

        with patch("src.repositories.signals.select"):
            with pytest.raises(DatabaseError):
                await repo.get_by_symbol("AAPL")

    @pytest.mark.asyncio
    async def test_get_latest_returns_none_for_no_results(self):
        session = _mock_session()
        session.execute.return_value = _scalar_result([])
        repo = TradingSignalRepository(session)

        with patch("src.repositories.signals.select"):
            result = await repo.get_latest("UNKNOWN")

        assert result is None


# ---------------------------------------------------------------------------
# PositionRepository
# ---------------------------------------------------------------------------

class TestPositionRepository:
    @pytest.mark.asyncio
    async def test_create_returns_id(self):
        session = _mock_session()
        fake_id = uuid.uuid4()
        repo = PositionRepository(session)

        with patch("src.repositories.positions.Position") as MockPos:
            instance = MagicMock()
            instance.id = fake_id
            MockPos.return_value = instance
            result = await repo.create({"symbol": "AAPL", "quantity": 1})

        assert result == str(fake_id)

    @pytest.mark.asyncio
    async def test_update_pnl_does_not_raise(self):
        session = _mock_session()
        fake_pos = MagicMock()
        fake_pos.unrealized_pnl = 0.0
        session.execute.return_value = _scalar_result([fake_pos])
        repo = PositionRepository(session)

        with patch("src.repositories.positions.select"):
            await repo.update_pnl(str(uuid.uuid4()), 250.0)

    @pytest.mark.asyncio
    async def test_update_pnl_raises_on_db_error(self):
        session = _mock_session()
        session.execute.side_effect = Exception("DB error")
        repo = PositionRepository(session)

        with patch("src.repositories.positions.select"):
            with pytest.raises(DatabaseError):
                await repo.update_pnl(str(uuid.uuid4()), 100.0)

    @pytest.mark.asyncio
    async def test_get_open_returns_list(self):
        session = _mock_session()
        fake_rows = [MagicMock(), MagicMock()]
        for row in fake_rows:
            row.__table__ = MagicMock()
            row.__table__.columns = []
        session.execute.return_value = _scalar_result(fake_rows)
        repo = PositionRepository(session)

        with patch("src.repositories.positions.select"):
            result = await repo.get_open("session-123")

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_by_id_returns_none_on_exception(self):
        session = _mock_session()
        session.execute.side_effect = Exception("not found")
        repo = PositionRepository(session)

        with patch("src.repositories.positions.select"):
            result = await repo.get_by_id(str(uuid.uuid4()))

        assert result is None

    @pytest.mark.asyncio
    async def test_close_returns_updated_record(self):
        session = _mock_session()
        fake_pos = MagicMock()
        fake_pos.__table__ = MagicMock()
        fake_pos.__table__.columns = []
        fake_pos.status = "open"
        session.execute.return_value = _scalar_result([fake_pos])
        repo = PositionRepository(session)

        with patch("src.repositories.positions.select"):
            result = await repo.close(str(uuid.uuid4()))

        assert fake_pos.status == "closed"

    @pytest.mark.asyncio
    async def test_close_raises_not_found_when_missing(self):
        session = _mock_session()
        session.execute.return_value = _scalar_result([])
        repo = PositionRepository(session)

        with patch("src.repositories.positions.select"):
            with pytest.raises(NotFoundError):
                await repo.close(str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# SessionRepository
# ---------------------------------------------------------------------------

class TestSessionRepository:
    @pytest.mark.asyncio
    async def test_create_returns_session(self):
        session = _mock_session()
        fake_row = MagicMock()
        fake_row.__table__ = MagicMock()
        fake_row.__table__.columns = []
        repo = SessionRepository(session)

        with patch("src.repositories.sessions.BrowserSession") as MockSess:
            MockSess.return_value = fake_row
            result = await repo.create({"session_token": "tok-abc"})

        session.add.assert_called_once_with(fake_row)

    @pytest.mark.asyncio
    async def test_get_returns_none_on_exception(self):
        session = _mock_session()
        session.execute.side_effect = Exception("conn error")
        repo = SessionRepository(session)

        with patch("src.repositories.sessions.select"):
            result = await repo.get("nonexistent-token")

        assert result is None

    @pytest.mark.asyncio
    async def test_touch_does_not_raise(self):
        session = _mock_session()
        fake_row = MagicMock()
        fake_row.last_accessed_at = None
        session.execute.return_value = _scalar_result([fake_row])
        repo = SessionRepository(session)

        with patch("src.repositories.sessions.select"):
            await repo.touch("some-token")


# ---------------------------------------------------------------------------
# StockRepository
# ---------------------------------------------------------------------------

class TestStockRepository:
    @pytest.mark.asyncio
    async def test_upsert_batch_empty_list_is_noop(self):
        session = _mock_session()
        repo = StockRepository(session)
        await repo.upsert_batch([])
        session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_upsert_batch_calls_execute(self):
        session = _mock_session()
        repo = StockRepository(session)

        with patch("src.repositories.stocks.pg_insert") as mock_insert:
            stmt = MagicMock()
            stmt.on_conflict_do_update.return_value = stmt
            mock_insert.return_value = stmt
            await repo.upsert_batch([{"symbol": "AAPL"}, {"symbol": "TSLA"}])

        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_trending_returns_list(self):
        session = _mock_session()
        fake_rows = [MagicMock(), MagicMock()]
        for row in fake_rows:
            row.__table__ = MagicMock()
            row.__table__.columns = []
        session.execute.return_value = _scalar_result(fake_rows)
        repo = StockRepository(session)

        with patch("src.repositories.stocks.select"):
            result = await repo.get_trending()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_trending_raises_on_db_error(self):
        session = _mock_session()
        session.execute.side_effect = Exception("DB error")
        repo = StockRepository(session)

        with patch("src.repositories.stocks.select"):
            with pytest.raises(DatabaseError):
                await repo.get_trending()
