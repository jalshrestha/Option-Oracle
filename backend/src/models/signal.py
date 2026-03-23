"""TradingSignal ORM model."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class TradingSignal(Base, TimestampMixin):
    __tablename__ = "trading_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    strength: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    decision_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    market_scenario: Mapped[str] = mapped_column(String(50), nullable=False)
    strategy_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSONB columns for flexible nested data
    agent_weights: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    technical_analysis: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    sentiment_analysis: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    flow_analysis: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    historical_analysis: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    strike_recommendations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)

    educational_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
