"""Cache ORM models for market data and AI analysis."""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class MarketDataCache(Base):
    __tablename__ = "market_data_cache"

    symbol: Mapped[str] = mapped_column(String(10), primary_key=True)
    price_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    technical_indicators: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    options_chain: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AiAnalysisCache(Base):
    __tablename__ = "ai_analysis_cache"

    symbol: Mapped[str] = mapped_column(String(10), primary_key=True)
    analysis_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
