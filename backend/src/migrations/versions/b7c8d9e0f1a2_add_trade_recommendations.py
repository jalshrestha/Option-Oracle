"""add trade recommendations

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-06-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "trade_recommendations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(length=255), nullable=False),
        sa.Column("symbol", sa.String(length=10), nullable=False),
        sa.Column("strategy", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("mode", sa.String(length=10), nullable=False),
        sa.Column("legs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rationale", sa.String(length=1000), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_analysis_id", sa.String(length=100), nullable=True),
        sa.Column("estimated_cost", sa.Float(), nullable=False),
        sa.Column("max_loss", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("executed_position_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_trade_recommendations_session_id"), "trade_recommendations", ["session_id"], unique=False)
    op.create_index(op.f("ix_trade_recommendations_status"), "trade_recommendations", ["status"], unique=False)
    op.create_index(op.f("ix_trade_recommendations_symbol"), "trade_recommendations", ["symbol"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_trade_recommendations_symbol"), table_name="trade_recommendations")
    op.drop_index(op.f("ix_trade_recommendations_status"), table_name="trade_recommendations")
    op.drop_index(op.f("ix_trade_recommendations_session_id"), table_name="trade_recommendations")
    op.drop_table("trade_recommendations")
