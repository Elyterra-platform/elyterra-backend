"""change_role_and_subscription_status_to_varchar

Revision ID: 82531de5a87c
Revises: e9e3c6b4b191
Create Date: 2025-10-22 20:36:29.402626

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '82531de5a87c'
down_revision: Union[str, Sequence[str], None] = 'e9e3c6b4b191'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change role and subscription_status from enum to varchar."""
    # Change role column from enum to varchar
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50) USING role::text")

    # Change subscription_status column from enum to varchar
    op.execute("ALTER TABLE users ALTER COLUMN subscription_status TYPE VARCHAR(50) USING subscription_status::text")


def downgrade() -> None:
    """Revert role and subscription_status back to enum."""
    # Revert role column to enum
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE user_role_enum USING role::user_role_enum")

    # Revert subscription_status column to enum
    op.execute("ALTER TABLE users ALTER COLUMN subscription_status TYPE subscription_status_enum USING subscription_status::subscription_status_enum")
