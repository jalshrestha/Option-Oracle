"""Order ORM model."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    position_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("positions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(10), nullable=False)  # buy/sell
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), default="market", nullable=False)
    limit_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    execution_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    broker_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    filled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
