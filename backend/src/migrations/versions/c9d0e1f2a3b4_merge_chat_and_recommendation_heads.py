"""merge chat history and trade recommendation heads

Revision ID: c9d0e1f2a3b4
Revises: b7c8d9e0f1a2, 8b4a6a0d2f34
Create Date: 2026-06-20

"""
from typing import Sequence, Union


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = ("b7c8d9e0f1a2", "8b4a6a0d2f34")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
