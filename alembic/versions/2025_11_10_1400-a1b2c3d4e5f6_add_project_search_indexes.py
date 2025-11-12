"""add_project_search_indexes

Revision ID: a1b2c3d4e5f6
Revises: e9e3c6b4b191
Create Date: 2025-11-10 14:00:00.000000

Add database indexes for optimized project search performance:
- Country and city filtering
- Visibility score sorting
- JSONB tag search with GIN index
- Created_at timestamp sorting
- Investment amount range queries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'e9e3c6b4b191'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add indexes for optimized project search
    """
    # Index for common search filters (country, city, status, visibility)
    op.create_index(
        'idx_projects_search',
        'projects',
        ['country', 'city', 'status', 'visibility_score'],
        unique=False
    )

    # GIN index for JSONB tags array (PostgreSQL specific)
    # Enables efficient tag search using @> operator
    op.execute(
        'CREATE INDEX idx_projects_tags_gin ON projects USING GIN (tags);'
    )

    # Index for sorting by visibility score (DESC for featured projects first)
    op.create_index(
        'idx_projects_visibility_desc',
        'projects',
        [sa.text('visibility_score DESC')],
        unique=False
    )

    # Index for sorting by created_at (DESC for newest first)
    op.create_index(
        'idx_projects_created_desc',
        'projects',
        [sa.text('created_at DESC')],
        unique=False
    )

    # Index for investment amount range queries
    op.create_index(
        'idx_projects_investment',
        'projects',
        ['total_investment_required'],
        unique=False
    )

    # Index for ROI estimate queries
    op.create_index(
        'idx_projects_roi',
        'projects',
        ['roi_estimate'],
        unique=False
    )

    # Index for access level filtering
    op.create_index(
        'idx_projects_access_level',
        'projects',
        ['access_level'],
        unique=False
    )

    # Composite index for property type and status
    op.create_index(
        'idx_projects_type_status',
        'projects',
        ['property_type', 'status'],
        unique=False
    )

    # Index for developer lookup
    op.create_index(
        'idx_projects_developer_id',
        'projects',
        ['developer_id'],
        unique=False
    )

    # Index for published projects only (partial index for performance)
    op.execute(
        "CREATE INDEX idx_projects_published ON projects (created_at DESC) WHERE status = 'published';"
    )


def downgrade() -> None:
    """
    Remove all search indexes
    """
    # Drop indexes in reverse order
    op.execute('DROP INDEX IF EXISTS idx_projects_published;')
    op.drop_index('idx_projects_developer_id', table_name='projects')
    op.drop_index('idx_projects_type_status', table_name='projects')
    op.drop_index('idx_projects_access_level', table_name='projects')
    op.drop_index('idx_projects_roi', table_name='projects')
    op.drop_index('idx_projects_investment', table_name='projects')
    op.drop_index('idx_projects_created_desc', table_name='projects')
    op.drop_index('idx_projects_visibility_desc', table_name='projects')
    op.execute('DROP INDEX IF EXISTS idx_projects_tags_gin;')
    op.drop_index('idx_projects_search', table_name='projects')
