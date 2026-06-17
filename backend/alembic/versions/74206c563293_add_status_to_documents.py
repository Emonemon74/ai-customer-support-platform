"""add status to documents

Revision ID: 74206c563293
Revises: 1b5029e34404
Create Date: 2026-06-17 17:30:31.055209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74206c563293'
down_revision: Union[str, Sequence[str], None] = '1b5029e34404'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("status", sa.String(length=50), nullable=False, server_default="UPLOADED"),
    )


def downgrade() -> None:
    op.drop_column("documents", "status")