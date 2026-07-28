from typing import Any

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import chat as chat_routes
from app.core.config import Settings
from app.services.n8n_client import N8nClientError


def test_chat_requires_authentication(
    unauthenticated_chat_client: TestClient,
) -> None:
    response = unauthenticated_chat_client.post(
        "/chat",
        json={
            "question": "VPN bağlantısı kuramıyorum.",
        },
    )

    assert response.status_code == 401


def test_chat_rejects_blank_question(
    chat_client: TestClient,
) -> None:
    response = chat_client.post(
        "/chat",
        json={
            "question": "   ",
        },
    )

    assert response.status_code == 422


def test_chat_rejects_question_over_schema_limit(
    chat_client: TestClient,
) -> None:
    response = chat_client.post(
        "/chat",
        json={
            "question": "a" * 1001,
        },
    )

    assert response.status_code == 422


def test_chat_respects_configured_question_limit(
    chat_client: TestClient,
    test_settings: Settings,
) -> None:
    test_settings.max_question_length = 10

    response = chat_client.post(
        "/chat",
        json={
            "question": "a" * 11,
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Soru çok uzun. Lütfen daha kısa bir soru girin.",
    }


def test_chat_returns_n8n_response(
    chat_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    captured_request: dict[str, Any] = {}

    async def fake_post_to_n8n(
        *,
        url: str,
        payload: dict[str, Any],
        timeout_seconds: float,
    ) -> dict[str, Any]:
        captured_request["url"] = url
        captured_request["payload"] = payload
        captured_request["timeout_seconds"] = timeout_seconds

        return {
            "answer": "- İnternet bağlantısını kontrol edin.",
            "sources": [
                {
                    "document_id": "vpn-guide",
                    "title": "VPN Kullanım Rehberi",
                    "category": "network",
                    "section_title": "Bağlantı Sorunları",
                    "chunk_index": 1,
                    "score": 0.25,
                }
            ],
            "response_type": "rag_answer",
        }

    monkeypatch.setattr(
        chat_routes,
        "post_to_n8n",
        fake_post_to_n8n,
    )

    response = chat_client.post(
        "/chat",
        json={
            "question": "  VPN bağlantısı kuramıyorum.  ",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "question": "VPN bağlantısı kuramıyorum.",
        "answer": "- İnternet bağlantısını kontrol edin.",
        "sources": [
            {
                "document_id": "vpn-guide",
                "title": "VPN Kullanım Rehberi",
                "category": "network",
                "section_title": "Bağlantı Sorunları",
                "chunk_index": 1,
                "source_file_name": None,
                "file_type": None,
                "score": 0.25,
            }
        ],
        "response_type": "rag_answer",
    }

    assert captured_request == {
        "url": "http://testserver/rag",
        "payload": {
            "question": "VPN bağlantısı kuramıyorum.",
        },
        "timeout_seconds": 5.0,
    }


def test_chat_replaces_invalid_sources_with_empty_list(
    chat_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    async def fake_post_to_n8n(**_kwargs: Any) -> dict[str, Any]:
        return {
            "question": "VPN bağlantısı kuramıyorum.",
            "answer": "- İnternet bağlantısını kontrol edin.",
            "sources": "invalid-source-value",
        }

    monkeypatch.setattr(
        chat_routes,
        "post_to_n8n",
        fake_post_to_n8n,
    )

    response = chat_client.post(
        "/chat",
        json={
            "question": "VPN bağlantısı kuramıyorum.",
        },
    )

    assert response.status_code == 200
    assert response.json()["sources"] == []


def test_chat_rejects_n8n_response_without_answer(
    chat_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    async def fake_post_to_n8n(**_kwargs: Any) -> dict[str, Any]:
        return {
            "question": "VPN bağlantısı kuramıyorum.",
            "sources": [],
        }

    monkeypatch.setattr(
        chat_routes,
        "post_to_n8n",
        fake_post_to_n8n,
    )

    response = chat_client.post(
        "/chat",
        json={
            "question": "VPN bağlantısı kuramıyorum.",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": "Chatbot servisinden geçerli bir cevap alınamadı.",
    }


def test_chat_handles_n8n_error_safely(
    chat_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    async def fake_post_to_n8n(**_kwargs: Any) -> dict[str, Any]:
        raise N8nClientError("Internal technical details.")

    monkeypatch.setattr(
        chat_routes,
        "post_to_n8n",
        fake_post_to_n8n,
    )

    response = chat_client.post(
        "/chat",
        json={
            "question": "VPN bağlantısı kuramıyorum.",
        },
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": (
            "Chatbot servisine şu anda ulaşılamıyor. "
            "Lütfen daha sonra tekrar deneyin."
        ),
    }

    assert "Internal technical details" not in response.text