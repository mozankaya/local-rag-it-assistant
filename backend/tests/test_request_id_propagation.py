from types import SimpleNamespace
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import chat as chat_routes
from app.api.routes.auth import get_current_user
from app.core.config import get_settings
from app.middleware.request_logging import (
    REQUEST_ID_HEADER,
    RequestLoggingMiddleware,
)


def test_chat_forwards_request_id_to_n8n(
    monkeypatch: MonkeyPatch,
) -> None:
    captured_call: dict[str, Any] = {}

    async def fake_post_to_n8n(
        *,
        url: str,
        payload: dict[str, Any],
        timeout_seconds: float,
        webhook_secret: str,
    ) -> dict[str, Any]:
        captured_call["url"] = url
        captured_call["payload"] = payload
        captured_call["timeout_seconds"] = timeout_seconds
        captured_call["webhook_secret"] = webhook_secret

        return {
            "chat_log_id": 42,
            "question": payload["question"],
            "answer": "- VPN bağlantısını kontrol edin.",
            "sources": [],
            "response_type": "rag_answer",
        }

    monkeypatch.setattr(
        chat_routes,
        "post_to_n8n",
        fake_post_to_n8n,
    )

    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)
    app.include_router(chat_routes.router)

    app.dependency_overrides[get_current_user] = lambda: object()

    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(
        max_question_length=1000,
        n8n_rag_webhook_url=("http://n8n.test/webhook/rag-query"),
        n8n_webhook_secret="test-webhook-secret",
        request_timeout_seconds=60.0,
        rag_top_k=5,
        rag_score_threshold=0.51,
        rag_max_sources=3,
    )

    with TestClient(app) as client:
        response = client.post(
            "/chat",
            headers={
                REQUEST_ID_HEADER: "test-request-123",
            },
            json={
                "question": ("VPN bağlantısı kuramıyorum."),
            },
        )

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "test-request-123"

    assert response.json()["chat_log_id"] == 42

    assert captured_call["payload"] == {
        "question": "VPN bağlantısı kuramıyorum.",
        "rag_settings": {
            "top_k": 5,
            "score_threshold": 0.51,
            "max_sources": 3,
        },
        "request_id": "test-request-123",
    }

    assert captured_call["url"] == ("http://n8n.test/webhook/rag-query")
    assert captured_call["timeout_seconds"] == 60.0
    assert captured_call["webhook_secret"] == "test-webhook-secret"
