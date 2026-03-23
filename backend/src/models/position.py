"""Position ORM model."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class Position(Base, TimestampMixin):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(20), default="option", nullable=False)

    # Option-specific fields (nullable for stocks)
    option_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # call/put
    strike_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    expiry_date: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    unrealized_pnl_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False, index=True)

    greeks: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
