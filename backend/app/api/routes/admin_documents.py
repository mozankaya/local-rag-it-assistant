from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes.users import require_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.admin_documents import (
    AdminDocumentResponse,
    DocumentCategoryResponse,
    PaginatedAdminDocumentsResponse,
)


router = APIRouter(
    prefix="/admin/documents",
    tags=["Admin Documents"],
)


def get_scalar_value(db: Session, query: str, params: dict | None = None) -> int:
    result = db.execute(text(query), params or {}).scalar()
    return int(result or 0)


@router.get("", response_model=PaginatedAdminDocumentsResponse)
def list_documents(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    search_value = search.strip() if search else None
    category_value = category.strip() if category else None

    params = {
        "limit": limit,
        "offset": offset,
        "search": search_value,
        "category": category_value,
    }

    total = get_scalar_value(
        db,
        """
        WITH documents AS (
            SELECT
                COALESCE(metadata->>'document_id', 'unknown') AS document_id,
                COALESCE(metadata->>'title', 'Başlıksız Doküman') AS title,
                COALESCE(metadata->>'category', 'unknown') AS category,
                COALESCE(metadata->>'file_type', 'unknown') AS file_type,
                COALESCE(
                    metadata->>'source_file_name',
                    metadata->>'file_name',
                    'unknown'
                ) AS source_file_name,
                MAX(metadata->>'last_updated') AS last_updated,
                COUNT(*) AS chunk_count
            FROM langchain_document_chunks
            GROUP BY
                COALESCE(metadata->>'document_id', 'unknown'),
                COALESCE(metadata->>'title', 'Başlıksız Doküman'),
                COALESCE(metadata->>'category', 'unknown'),
                COALESCE(metadata->>'file_type', 'unknown'),
                COALESCE(
                    metadata->>'source_file_name',
                    metadata->>'file_name',
                    'unknown'
                )
        )
        SELECT COUNT(*)
        FROM documents
        WHERE
            (
                CAST(:category AS text) IS NULL
                OR category = :category
            )
            AND
            (
                CAST(:search AS text) IS NULL
                OR document_id ILIKE '%' || :search || '%'
                OR title ILIKE '%' || :search || '%'
                OR category ILIKE '%' || :search || '%'
                OR source_file_name ILIKE '%' || :search || '%'
            )
        """,
        {
            "search": search_value,
            "category": category_value,
        },
    )

    rows = db.execute(
        text(
            """
            WITH documents AS (
                SELECT
                    COALESCE(metadata->>'document_id', 'unknown') AS document_id,
                    COALESCE(metadata->>'title', 'Başlıksız Doküman') AS title,
                    COALESCE(metadata->>'category', 'unknown') AS category,
                    COALESCE(metadata->>'file_type', 'unknown') AS file_type,
                    COALESCE(
                        metadata->>'source_file_name',
                        metadata->>'file_name',
                        'unknown'
                    ) AS source_file_name,
                    MAX(metadata->>'last_updated') AS last_updated,
                    COUNT(*) AS chunk_count
                FROM langchain_document_chunks
                GROUP BY
                    COALESCE(metadata->>'document_id', 'unknown'),
                    COALESCE(metadata->>'title', 'Başlıksız Doküman'),
                    COALESCE(metadata->>'category', 'unknown'),
                    COALESCE(metadata->>'file_type', 'unknown'),
                    COALESCE(
                        metadata->>'source_file_name',
                        metadata->>'file_name',
                        'unknown'
                    )
            )
            SELECT *
            FROM documents
            WHERE
                (
                    CAST(:category AS text) IS NULL
                    OR category = :category
                )
                AND
                (
                    CAST(:search AS text) IS NULL
                    OR document_id ILIKE '%' || :search || '%'
                    OR title ILIKE '%' || :search || '%'
                    OR category ILIKE '%' || :search || '%'
                    OR source_file_name ILIKE '%' || :search || '%'
                )
            ORDER BY category ASC, title ASC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    items = [
        AdminDocumentResponse(
            document_id=row["document_id"],
            title=row["title"],
            category=row["category"],
            file_type=row["file_type"],
            source_file_name=row["source_file_name"],
            last_updated=row["last_updated"],
            chunk_count=int(row["chunk_count"]),
        )
        for row in rows
    ]

    return PaginatedAdminDocumentsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total,
    )


@router.get("/categories", response_model=list[DocumentCategoryResponse])
def list_document_categories(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    rows = db.execute(
        text(
            """
            WITH documents AS (
                SELECT DISTINCT
                    COALESCE(metadata->>'document_id', 'unknown') AS document_id,
                    COALESCE(metadata->>'category', 'unknown') AS category
                FROM langchain_document_chunks
            )
            SELECT
                category,
                COUNT(*) AS document_count
            FROM documents
            GROUP BY category
            ORDER BY category ASC
            """
        )
    ).mappings().all()

    return [
        DocumentCategoryResponse(
            category=row["category"],
            document_count=int(row["document_count"]),
        )
        for row in rows
    ]