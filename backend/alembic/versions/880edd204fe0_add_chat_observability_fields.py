"""add chat observability fields

Revision ID: 880edd204fe0
Revises: 
Create Date: 2026-07-29 10:33:10.627297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '880edd204fe0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chat_logs",
        sa.Column(
            "request_id",
            sa.String(length=100),
            nullable=True,
        ),
        schema="public",
    )

    op.add_column(
        "chat_logs",
        sa.Column(
            "duration_ms",
            sa.Numeric(
                precision=12,
                scale=2,
            ),
            nullable=True,
        ),
        schema="public",
    )

    op.add_column(
        "chat_logs",
        sa.Column(
            "source_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        schema="public",
    )

    op.create_index(
        "idx_chat_logs_request_id",
        "chat_logs",
        ["request_id"],
        unique=False,
        schema="public",
    )


def downgrade() -> None:
    op.drop_index(
        "idx_chat_logs_request_id",
        table_name="chat_logs",
        schema="public",
    )

    op.drop_column(
        "chat_logs",
        "source_count",
        schema="public",
    )

    op.drop_column(
        "chat_logs",
        "duration_ms",
        schema="public",
    )

    op.drop_column(
        "chat_logs",
        "request_id",
        schema="public",
    )
