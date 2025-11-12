"""add_investor_only_to_access_level_enum

Revision ID: 24f17e6f0d2f
Revises: a257c57601f9
Create Date: 2025-11-12 05:53:57.449613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '24f17e6f0d2f'
down_revision: Union[str, Sequence[str], None] = 'a257c57601f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add 'investor_only' value to access_level_enum
    op.execute("ALTER TYPE access_level_enum ADD VALUE IF NOT EXISTS 'investor_only'")


def downgrade() -> None:
    """Downgrade schema."""
    # Note: PostgreSQL doesn't support removing enum values
    # Would need to recreate the enum type to remove the value
    pass
