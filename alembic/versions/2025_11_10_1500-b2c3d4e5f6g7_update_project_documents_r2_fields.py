"""update_project_documents_r2_fields

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-11-10 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add R2-specific fields to project_documents table"""

    # Add new columns
    op.add_column('project_documents', sa.Column('file_name', sa.String(length=255), nullable=True))
    op.add_column('project_documents', sa.Column('r2_key', sa.String(length=500), nullable=True))
    op.add_column('project_documents', sa.Column('file_size', sa.Integer(), nullable=True))

    # Rename checksum to checksum_sha256
    op.alter_column('project_documents', 'checksum',
                    new_column_name='checksum_sha256',
                    existing_type=sa.String(length=64),
                    existing_nullable=True)

    # After migration, these columns should be made NOT NULL in production
    # after backfilling existing data


def downgrade() -> None:
    """Remove R2-specific fields from project_documents table"""

    # Rename checksum_sha256 back to checksum
    op.alter_column('project_documents', 'checksum_sha256',
                    new_column_name='checksum',
                    existing_type=sa.String(length=64),
                    existing_nullable=True)

    # Drop new columns
    op.drop_column('project_documents', 'file_size')
    op.drop_column('project_documents', 'r2_key')
    op.drop_column('project_documents', 'file_name')
