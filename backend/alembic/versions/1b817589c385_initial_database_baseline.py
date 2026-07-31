"""initial database baseline

Revision ID: 1b817589c385
Revises:
Create Date: 2026-07-31 09:47:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "1b817589c385"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the initial database objects required by the application."""


    op.execute(
        """
        CREATE EXTENSION vector;
        """
    )


    op.create_table(
        "n8n_vector_collections",
        sa.Column(
            "uuid",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "name",
            sa.String(),
            nullable=True,
        ),
        sa.Column(
            "cmetadata",
            postgresql.JSONB(),
            nullable=True,
        ),
        schema="public",
    )

    op.create_index(
        "idx_n8n_vector_collections_name",
        "n8n_vector_collections",
        ["name"],
        unique=False,
        schema="public",
    )


    op.execute(
        """
        CREATE TABLE public.langchain_document_chunks
        (
            id UUID NOT NULL DEFAULT gen_random_uuid(),
            text TEXT NULL,
            metadata JSONB NULL,
            embedding VECTOR NULL,
            collection_id UUID NULL,

            CONSTRAINT langchain_document_chunks_pkey
                PRIMARY KEY (id),

            CONSTRAINT langchain_document_chunks_collection_id_fkey
                FOREIGN KEY (collection_id)
                REFERENCES public.n8n_vector_collections(uuid)
                ON DELETE CASCADE
        );
        """
    )


    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "full_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "hashed_password",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=True,
            server_default=sa.text("now()"),
        ),
        schema="public",
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
        schema="public",
    )

    op.create_index(
        "ix_users_id",
        "users",
        ["id"],
        unique=False,
        schema="public",
    )


    op.create_table(
        "chat_logs",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "question",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "answer",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "sources",
            postgresql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "category",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "section_title",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "response_type",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        schema="public",
    )

    op.create_index(
        "idx_chat_logs_category",
        "chat_logs",
        ["category"],
        unique=False,
        schema="public",
    )

    op.create_index(
        "idx_chat_logs_created_at",
        "chat_logs",
        ["created_at"],
        unique=False,
        schema="public",
    )

    op.create_index(
        "idx_chat_logs_section_title",
        "chat_logs",
        ["section_title"],
        unique=False,
        schema="public",
    )


    op.create_table(
        "feedback_logs",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "question",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "answer",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "feedback",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "sources",
            postgresql.JSONB(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=False),
            nullable=True,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "feedback IN ('useful', 'not_useful')",
            name="feedback_logs_feedback_check",
        ),
        schema="public",
    )


def downgrade() -> None:
    """Remove the initial database objects.

    Bu downgrade temel uygulama tablolarını ve verilerini kaldırır.
    Dolu bir veritabanında rutin rollback yöntemi olarak kullanılmamalıdır.
    """


    op.drop_table(
        "feedback_logs",
        schema="public",
    )

    op.drop_index(
        "idx_chat_logs_section_title",
        table_name="chat_logs",
        schema="public",
    )

    op.drop_index(
        "idx_chat_logs_created_at",
        table_name="chat_logs",
        schema="public",
    )

    op.drop_index(
        "idx_chat_logs_category",
        table_name="chat_logs",
        schema="public",
    )

    op.drop_table(
        "chat_logs",
        schema="public",
    )

    op.drop_index(
        "ix_users_id",
        table_name="users",
        schema="public",
    )

    op.drop_index(
        "ix_users_email",
        table_name="users",
        schema="public",
    )

    op.drop_table(
        "users",
        schema="public",
    )


    op.drop_table(
        "langchain_document_chunks",
        schema="public",
    )

    op.drop_index(
        "idx_n8n_vector_collections_name",
        table_name="n8n_vector_collections",
        schema="public",
    )

    op.drop_table(
        "n8n_vector_collections",
        schema="public",
    )


    op.execute(
        """
        DROP EXTENSION vector;
        """
    )