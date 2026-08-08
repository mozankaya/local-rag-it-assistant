from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes import admin_dashboard as dashboard_routes
from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.models.user import User


class FakeResult:
    """SQLAlchemy sorgu sonucunun testlerde gereken küçük karşılığı."""

    def __init__(
        self,
        *,
        scalar_result: int | None = 0,
        rows: list[dict[str, Any]] | None = None,
    ) -> None:
        self.scalar_result = scalar_result
        self.rows = rows or []

    def scalar(self) -> int | None:
        return self.scalar_result

    def mappings(self) -> "FakeResult":
        return self

    def all(self) -> list[dict[str, Any]]:
        return self.rows


class FakeSession:
    """Endpoint'in çalıştırdığı sorguları ve parametreleri kaydeder."""

    def __init__(self, *results: FakeResult) -> None:
        self.results = list(results)
        self.execute_calls: list[dict[str, Any]] = []

    def execute(
        self,
        query: Any,
        params: dict[str, Any] | None = None,
    ) -> FakeResult:
        self.execute_calls.append(
            {
                "query": str(query),
                "params": params or {},
            }
        )

        if self.results:
            return self.results.pop(0)

        return FakeResult()


def create_user(*, role: str = "admin") -> User:
    return User(
        id=1,
        email=f"{role}@example.com",
        full_name=f"Test {role.title()}",
        hashed_password="fake-hashed-password",
        role=role,
        is_active=True,
    )


def create_client(
    *,
    current_user: User,
    fake_db: FakeSession,
) -> TestClient:
    """Dashboard router'ını bağımlılıkları değiştirilmiş test uygulamasına ekler."""

    app = FastAPI()
    app.include_router(dashboard_routes.router)

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_db] = lambda: fake_db

    return TestClient(app)


def test_normal_user_cannot_access_admin_dashboard() -> None:
    fake_db = FakeSession()

    with create_client(
        current_user=create_user(role="user"),
        fake_db=fake_db,
    ) as client:
        response = client.get("/admin/dashboard/summary")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Only admin users can perform this action.",
    }

    assert fake_db.execute_calls == []


def test_admin_can_get_dashboard_summary() -> None:
    fake_db = FakeSession(
        FakeResult(scalar_result=120),  # total_questions
        FakeResult(scalar_result=8),    # today_questions
        FakeResult(scalar_result=30),   # total_feedback
        FakeResult(scalar_result=22),   # useful_feedback
        FakeResult(scalar_result=8),    # not_useful_feedback
        FakeResult(scalar_result=5),    # no_relevant_source_count
        FakeResult(scalar_result=3),    # out_of_scope_count
        FakeResult(scalar_result=2),    # llm_error_count
        FakeResult(scalar_result=10),   # total_users
        FakeResult(scalar_result=2),    # admin_users
        FakeResult(scalar_result=8),    # standard_users
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get("/admin/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total_questions": 120,
        "today_questions": 8,
        "total_feedback": 30,
        "useful_feedback": 22,
        "not_useful_feedback": 8,
        "no_relevant_source_count": 5,
        "out_of_scope_count": 3,
        "llm_error_count": 2,
        "total_users": 10,
        "admin_users": 2,
        "standard_users": 8,
    }

    assert len(fake_db.execute_calls) == 11

    assert (
        "SELECT COUNT(*) FROM chat_logs"
        in fake_db.execute_calls[0]["query"]
    )
    assert (
        "created_at::date = CURRENT_DATE"
        in fake_db.execute_calls[1]["query"]
    )
    assert (
        "WHERE role = 'admin'"
        in fake_db.execute_calls[9]["query"]
    )
    assert (
        "WHERE role = 'user'"
        in fake_db.execute_calls[10]["query"]
    )


def test_dashboard_summary_returns_zero_for_empty_database() -> None:
    # FakeSession returns zero for each query when no results are queued.
    fake_db = FakeSession()

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get("/admin/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total_questions": 0,
        "today_questions": 0,
        "total_feedback": 0,
        "useful_feedback": 0,
        "not_useful_feedback": 0,
        "no_relevant_source_count": 0,
        "out_of_scope_count": 0,
        "llm_error_count": 0,
        "total_users": 0,
        "admin_users": 0,
        "standard_users": 0,
    }

    assert len(fake_db.execute_calls) == 11


def test_admin_can_get_response_type_counts() -> None:
    fake_db = FakeSession(
        FakeResult(
            rows=[
                {
                    "response_type": "success",
                    "count": 75,
                },
                {
                    "response_type": "no_relevant_source",
                    "count": 12,
                },
                {
                    "response_type": "unknown",
                    "count": 3,
                },
            ]
        )
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get(
            "/admin/dashboard/response-types"
        )

    assert response.status_code == 200
    assert response.json() == [
        {
            "response_type": "success",
            "count": 75,
        },
        {
            "response_type": "no_relevant_source",
            "count": 12,
        },
        {
            "response_type": "unknown",
            "count": 3,
        },
    ]

    assert (
        "GROUP BY COALESCE(response_type, 'unknown')"
        in fake_db.execute_calls[0]["query"]
    )


def test_admin_can_get_category_counts() -> None:
    fake_db = FakeSession(
        FakeResult(
            rows=[
                {
                    "category": "network",
                    "count": 40,
                },
                {
                    "category": "account",
                    "count": 25,
                },
            ]
        )
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get("/admin/dashboard/categories")

    assert response.status_code == 200
    assert response.json() == [
        {
            "category": "network",
            "count": 40,
        },
        {
            "category": "account",
            "count": 25,
        },
    ]

    assert (
        "WHERE response_type = 'rag_answer'"
        in fake_db.execute_calls[0]["query"]
    )
    assert (
        "AND category IS NOT NULL"
        in fake_db.execute_calls[0]["query"]
    )


def test_admin_can_get_feedback_summary() -> None:
    fake_db = FakeSession(
        FakeResult(scalar_result=15),
        FakeResult(scalar_result=11),
        FakeResult(scalar_result=4),
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get(
            "/admin/dashboard/feedback-summary"
        )

    assert response.status_code == 200
    assert response.json() == {
        "total_feedback": 15,
        "useful_feedback": 11,
        "not_useful_feedback": 4,
    }

    assert len(fake_db.execute_calls) == 3


def test_admin_can_get_paginated_recent_questions() -> None:
    created_at = datetime(
        2026,
        7,
        31,
        7,
        30,
        tzinfo=timezone.utc,
    )

    fake_db = FakeSession(
        FakeResult(scalar_result=5),
        FakeResult(
            rows=[
                {
                    "id": 7,
                    "question": "VPN bağlantısı kuramıyorum.",
                    "answer_preview": "VPN ayarlarını kontrol edin.",
                    "category": "network",
                    "section_title": "VPN Bağlantı Sorunları",
                    "response_type": "success",
                    "created_at": created_at,
                },
                {
                    "id": 6,
                    "question": "Şifremi nasıl sıfırlarım?",
                    "answer_preview": "Şifre sıfırlama ekranını kullanın.",
                    "category": "account",
                    "section_title": "Şifre İşlemleri",
                    "response_type": "success",
                    "created_at": created_at,
                },
            ]
        ),
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get(
            "/admin/dashboard/recent-questions",
            params={
                "limit": 2,
                "offset": 1,
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 1
    assert body["has_more"] is True

    assert len(body["items"]) == 2
    assert body["items"][0]["id"] == 7
    assert body["items"][0]["category"] == "network"
    assert body["items"][0]["response_type"] == "success"

    assert fake_db.execute_calls[1]["params"] == {
        "limit": 2,
        "offset": 1,
    }

    assert (
        "ORDER BY created_at DESC"
        in fake_db.execute_calls[1]["query"]
    )


def test_admin_can_filter_review_items() -> None:
    created_at = datetime(
        2026,
        7,
        31,
        8,
        0,
        tzinfo=timezone.utc,
    )

    fake_db = FakeSession(
        FakeResult(scalar_result=1),
        FakeResult(
            rows=[
                {
                    "item_type": "chat_log",
                    "item_id": 14,
                    "review_reason": "llm_error",
                    "question": "Test sorusu",
                    "answer_preview": "LLM cevabı üretilemedi.",
                    "feedback": None,
                    "response_type": "llm_error",
                    "category": "network",
                    "section_title": None,
                    "created_at": created_at,
                }
            ]
        ),
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get(
            "/admin/dashboard/review-items",
            params={
                "limit": 10,
                "offset": 0,
                "review_reason": "llm_error",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert body["has_more"] is False
    assert len(body["items"]) == 1

    item = body["items"][0]

    assert item["item_type"] == "chat_log"
    assert item["item_id"] == 14
    assert item["review_reason"] == "llm_error"
    assert item["question"] == "Test sorusu"
    assert item["answer_preview"] == "LLM cevabı üretilemedi."
    assert item["feedback"] is None
    assert item["response_type"] == "llm_error"
    assert item["category"] == "network"
    assert item["section_title"] is None

    serialized_created_at = datetime.fromisoformat(
        item["created_at"].replace("Z", "+00:00")
    )

    assert serialized_created_at == created_at

    assert fake_db.execute_calls[0]["params"] == {
        "review_reason": "llm_error",
    }

    assert fake_db.execute_calls[1]["params"] == {
        "limit": 10,
        "offset": 0,
        "review_reason": "llm_error",
    }


def test_review_items_rejects_invalid_review_reason() -> None:
    fake_db = FakeSession()

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get(
            "/admin/dashboard/review-items",
            params={
                "review_reason": "invalid-reason",
            },
        )

    assert response.status_code == 422

    assert fake_db.execute_calls == []
