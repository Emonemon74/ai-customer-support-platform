"""add sources to messages

Persists the citations of an assistant answer so they survive a reload.

Revision ID: c3d9e5f1a7b2
Revises: b7e1a2c4d5f6
Create Date: 2026-10-27 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d9e5f1a7b2"
down_revision: str | Sequence[str] | None = "b7e1a2c4d5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("sources", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "sources")
