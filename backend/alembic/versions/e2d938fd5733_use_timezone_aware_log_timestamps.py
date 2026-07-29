"""use timezone aware log timestamps

Revision ID: e2d938fd5733
Revises: 880edd204fe0
Create Date: 2026-07-29 15:10:00.547700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2d938fd5733'
down_revision: Union[str, Sequence[str], None] = '880edd204fe0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "chat_logs",
        "created_at",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using=(
            "created_at AT TIME ZONE 'UTC'"
        ),
        schema="public",
    )

    op.alter_column(
        "feedback_logs",
        "created_at",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=True),
        existing_nullable=True,
        postgresql_using=(
            "created_at AT TIME ZONE 'UTC'"
        ),
        schema="public",
    )


def downgrade() -> None:
    op.alter_column(
        "feedback_logs",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=True,
        postgresql_using=(
            "created_at AT TIME ZONE 'UTC'"
        ),
        schema="public",
    )

    op.alter_column(
        "chat_logs",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=True,
        postgresql_using=(
            "created_at AT TIME ZONE 'UTC'"
        ),
        schema="public",
    )
