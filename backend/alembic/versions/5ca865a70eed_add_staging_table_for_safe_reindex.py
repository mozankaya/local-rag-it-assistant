"""add staging table for safe reindex

Revision ID: 5ca865a70eed
Revises: e2d938fd5733
Create Date: 2026-07-29 15:25:26.821755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5ca865a70eed'
down_revision: Union[str, Sequence[str], None] = 'e2d938fd5733'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Güvenli reindex işlemi için ana PGVector tablosuyla
    aynı yapıda boş bir staging tablosu oluşturur.
    """

    op.execute(
        """
        CREATE TABLE public.langchain_document_chunks_staging
        (
            LIKE public.langchain_document_chunks
            INCLUDING ALL
        );
        """
    )

    op.execute(
        """
        ALTER TABLE public.langchain_document_chunks_staging
        ADD CONSTRAINT
            langchain_document_chunks_staging_collection_id_fkey
        FOREIGN KEY (collection_id)
        REFERENCES public.n8n_vector_collections(uuid)
        ON DELETE CASCADE;
        """
    )


def downgrade() -> None:
    """
    Güvenli reindex staging tablosunu kaldırır.
    """

    op.execute(
        """
        DROP TABLE public.langchain_document_chunks_staging;
        """
    )