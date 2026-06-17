"""rename content type to file type

Revision ID: 1b5029e34404
Revises: c05a04a07654
Create Date: 2026-06-17 17:21:16.420352

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b5029e34404'
down_revision: Union[str, Sequence[str], None] = 'c05a04a07654'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
