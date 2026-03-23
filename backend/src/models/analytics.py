"""Analytics and system config ORM models."""
import uuid
from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import Date, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class TradingAnalytics(Base, TimestampMixin):
    __tablename__ = "trading_analytics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    winning_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losing_trades: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_win: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    avg_loss: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    symbols_traded: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    strategy_breakdown: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class SystemSnapshot(Base, TimestampMixin):
    __tablename__ = "system_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    snapshot_date: Mapped[date] = mapped_column(Date, unique=True, nullable=False)
    active_sessions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_signals: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_positions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    aggregate_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class SystemConfig(Base, TimestampMixin):
    __tablename__ = "system_config"

    config_key: Mapped[str] = mapped_column(String(100), primary_key=True)
    config_value: Mapped[Any] = mapped_column(JSONB, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
