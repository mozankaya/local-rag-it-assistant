"""add user deactivation timestamp

Revision ID: f75a04117ea0
Revises: 4f3abf8d6a1c
Create Date: 2026-08-04 14:36:26.391414

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f75a04117ea0'
down_revision: Union[str, Sequence[str], None] = '4f3abf8d6a1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the timestamp used for inactive-user retention."""

    op.add_column(
        "users",
        sa.Column(
            "deactivated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        schema="public",
    )

    op.execute("""
        UPDATE public.users
        SET deactivated_at = now()
        WHERE is_active IS FALSE
          AND deactivated_at IS NULL;
        """)


def downgrade() -> None:
    """Remove the inactive-user retention timestamp."""

    op.drop_column(
        "users",
        "deactivated_at",
        schema="public",
    )
