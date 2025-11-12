"""add_published_at_to_projects

Revision ID: c3277786fbd8
Revises: 24f17e6f0d2f
Create Date: 2025-11-12 07:33:01.581292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3277786fbd8'
down_revision: Union[str, Sequence[str], None] = '24f17e6f0d2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add published_at column to projects table
    op.add_column('projects', sa.Column('published_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove published_at column from projects table
    op.drop_column('projects', 'published_at')
