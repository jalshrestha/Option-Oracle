"""Stock reference data ORM model."""
from typing import Optional

from sqlalchemy import BigInteger, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base, TimestampMixin


class Stock(Base, TimestampMixin):
    __tablename__ = "stocks"

    symbol: Mapped[str] = mapped_column(String(10), primary_key=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    market_cap: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_options_enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
