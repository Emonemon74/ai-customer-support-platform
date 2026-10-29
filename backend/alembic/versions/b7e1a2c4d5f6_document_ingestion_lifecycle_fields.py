"""document ingestion lifecycle fields

Adds failure_reason, content_hash and updated_at to documents and moves the
default status from "UPLOADED" to "QUEUED".

Revision ID: b7e1a2c4d5f6
Revises: 8a7648c7b7e5
Create Date: 2026-09-08 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7e1a2c4d5f6"
down_revision: str | Sequence[str] | None = "8a7648c7b7e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents", sa.Column("failure_reason", sa.Text(), nullable=True)
    )
    op.add_column(
        "documents", sa.Column("content_hash", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "documents",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_documents_content_hash", "documents", ["content_hash"]
    )
    op.alter_column(
        "documents",
        "status",
        existing_type=sa.String(length=50),
        server_default="QUEUED",
    )


def downgrade() -> None:
    op.alter_column(
        "documents",
        "status",
        existing_type=sa.String(length=50),
        server_default="UPLOADED",
    )
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_column("documents", "updated_at")
    op.drop_column("documents", "content_hash")
    op.drop_column("documents", "failure_reason")
