"""merge_r2_migration

Revision ID: a257c57601f9
Revises: 82531de5a87c, b2c3d4e5f6g7
Create Date: 2025-11-11 07:50:51.430996

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a257c57601f9'
down_revision: Union[str, Sequence[str], None] = ('82531de5a87c', 'b2c3d4e5f6g7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
