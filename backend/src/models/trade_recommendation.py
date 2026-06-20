"""Trade recommendation ORM model."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class TradeRecommendation(Base, TimestampMixin):
    __tablename__ = "trade_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    action: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(10), default="paper", nullable=False)

    legs: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    rationale: Mapped[str] = mapped_column(String(1000), nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="rule_based", nullable=False)
    source_analysis_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    max_loss: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    executed_position_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
