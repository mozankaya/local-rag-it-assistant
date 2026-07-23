from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes.users import require_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.admin_dashboard import (
    CategoryCount,
    DashboardSummaryResponse,
    FeedbackSummaryResponse,
    PaginatedRecentQuestionsResponse,
    RecentQuestionResponse,
    ResponseTypeCount,
)


router = APIRouter(
    prefix="/admin/dashboard",
    tags=["Admin Dashboard"],
)


def get_scalar_value(db: Session, query: str, params: dict | None = None) -> int:
    result = db.execute(text(query), params or {}).scalar()
    return int(result or 0)


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    total_questions = get_scalar_value(db, "SELECT COUNT(*) FROM chat_logs")

    today_questions = get_scalar_value(
        db,
        """
        SELECT COUNT(*)
        FROM chat_logs
        WHERE created_at::date = CURRENT_DATE
        """,
    )

    total_feedback = get_scalar_value(db, "SELECT COUNT(*) FROM feedback_logs")

    useful_feedback = get_scalar_value(
        db,
        """
        SELECT COUNT(*)
        FROM feedback_logs
        WHERE feedback = 'useful'
        """,
    )

    not_useful_feedback = get_scalar_value(
        db,
        """
        SELECT COUNT(*)
        FROM feedback_logs
        WHERE feedback = 'not_useful'
        """,
    )

    no_relevant_source_count = get_scalar_value(
        db,
        """
        SELECT COUNT(*)
        FROM chat_logs
        WHERE response_type = 'no_relevant_source'
        """,
    )

    out_of_scope_count = get_scalar_value(
        db,
        """
        SELECT COUNT(*)
        FROM chat_logs
        WHERE response_type = 'out_of_scope'
        """,
    )

    llm_error_count = get_scalar_value(
        db,
        """
        SELECT COUNT(*)
        FROM chat_logs
        WHERE response_type = 'llm_error'
        """,
    )

    total_users = get_scalar_value(db, "SELECT COUNT(*) FROM users")

    admin_users = get_scalar_value(
        db,
        """
        SELECT COUNT(*)
        FROM users
        WHERE role = 'admin'
        """,
    )

    standard_users = get_scalar_value(
        db,
        """
        SELECT COUNT(*)
        FROM users
        WHERE role = 'user'
        """,
    )

    return DashboardSummaryResponse(
        total_questions=total_questions,
        today_questions=today_questions,
        total_feedback=total_feedback,
        useful_feedback=useful_feedback,
        not_useful_feedback=not_useful_feedback,
        no_relevant_source_count=no_relevant_source_count,
        out_of_scope_count=out_of_scope_count,
        llm_error_count=llm_error_count,
        total_users=total_users,
        admin_users=admin_users,
        standard_users=standard_users,
    )


@router.get("/response-types", response_model=list[ResponseTypeCount])
def get_response_type_counts(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    rows = db.execute(
        text(
            """
            SELECT
                COALESCE(response_type, 'unknown') AS response_type,
                COUNT(*) AS count
            FROM chat_logs
            GROUP BY COALESCE(response_type, 'unknown')
            ORDER BY count DESC
            """
        )
    ).mappings().all()

    return [
        ResponseTypeCount(
            response_type=row["response_type"],
            count=int(row["count"]),
        )
        for row in rows
    ]


@router.get("/categories", response_model=list[CategoryCount])
def get_category_counts(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    rows = db.execute(
        text(
            """
            SELECT
                COALESCE(category, 'unknown') AS category,
                COUNT(*) AS count
            FROM chat_logs
            GROUP BY COALESCE(category, 'unknown')
            ORDER BY count DESC
            """
        )
    ).mappings().all()

    return [
        CategoryCount(
            category=row["category"],
            count=int(row["count"]),
        )
        for row in rows
    ]


@router.get("/feedback-summary", response_model=FeedbackSummaryResponse)
def get_feedback_summary(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    total_feedback = get_scalar_value(db, "SELECT COUNT(*) FROM feedback_logs")

    useful_feedback = get_scalar_value(
        db,
        """
        SELECT COUNT(*)
        FROM feedback_logs
        WHERE feedback = 'useful'
        """,
    )

    not_useful_feedback = get_scalar_value(
        db,
        """
        SELECT COUNT(*)
        FROM feedback_logs
        WHERE feedback = 'not_useful'
        """,
    )

    return FeedbackSummaryResponse(
        total_feedback=total_feedback,
        useful_feedback=useful_feedback,
        not_useful_feedback=not_useful_feedback,
    )


@router.get("/recent-questions", response_model=PaginatedRecentQuestionsResponse)
def get_recent_questions(
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    total = get_scalar_value(db, "SELECT COUNT(*) FROM chat_logs")

    rows = db.execute(
        text(
            """
            SELECT
                id,
                question,
                LEFT(answer, 300) AS answer_preview,
                category,
                section_title,
                response_type,
                created_at
            FROM chat_logs
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {
            "limit": limit,
            "offset": offset,
        },
    ).mappings().all()

    items = [
        RecentQuestionResponse(
            id=row["id"],
            question=row["question"],
            answer_preview=row["answer_preview"],
            category=row["category"],
            section_title=row["section_title"],
            response_type=row["response_type"],
            created_at=row["created_at"],
        )
        for row in rows
    ]

    return PaginatedRecentQuestionsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total,
    )