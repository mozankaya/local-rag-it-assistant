"""link feedback to chat request

Revision ID: 4f3abf8d6a1c
Revises: 5ca865a70eed
Create Date: 2026-08-03 09:53:00.829060
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "4f3abf8d6a1c"
down_revision: Union[str, Sequence[str], None] = "5ca865a70eed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Link feedback records to their related chat log."""

    op.add_column(
        "feedback_logs",
        sa.Column(
            "chat_log_id",
            sa.Integer(),
            nullable=True,
        ),
        schema="public",
    )

    op.create_unique_constraint(
        "uq_feedback_logs_chat_log_id",
        "feedback_logs",
        ["chat_log_id"],
        schema="public",
    )

    op.create_foreign_key(
        "fk_feedback_logs_chat_log_id_chat_logs",
        "feedback_logs",
        "chat_logs",
        ["chat_log_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Remove the feedback-to-chat-log relationship."""

    op.drop_constraint(
        "fk_feedback_logs_chat_log_id_chat_logs",
        "feedback_logs",
        type_="foreignkey",
        schema="public",
    )

    op.drop_constraint(
        "uq_feedback_logs_chat_log_id",
        "feedback_logs",
        type_="unique",
        schema="public",
    )

    op.drop_column(
        "feedback_logs",
        "chat_log_id",
        schema="public",
    )
