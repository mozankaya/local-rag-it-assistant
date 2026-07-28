from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import feedback as feedback_routes
from app.services.n8n_client import N8nClientError


def valid_feedback_payload(
    feedback: str = "useful",
) -> dict[str, Any]:
    return {
        "question": "VPN bağlantısı kuramıyorum.",
        "answer": "- İnternet bağlantınızı kontrol edin.",
        "feedback": feedback,
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
    }


def test_feedback_requires_authentication(
    unauthenticated_feedback_client: TestClient,
) -> None:
    response = unauthenticated_feedback_client.post(
        "/feedback",
        json=valid_feedback_payload(),
    )

    assert response.status_code == 401


def test_feedback_rejects_invalid_feedback_value(
    feedback_client: TestClient,
) -> None:
    response = feedback_client.post(
        "/feedback",
        json=valid_feedback_payload(feedback="maybe"),
    )

    assert response.status_code == 422


def test_feedback_rejects_blank_question(
    feedback_client: TestClient,
) -> None:
    payload = valid_feedback_payload()
    payload["question"] = "   "

    response = feedback_client.post(
        "/feedback",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "feedback_value",
    [
        "useful",
        "not_useful",
    ],
)
def test_feedback_sends_payload_to_n8n(
    feedback_client: TestClient,
    monkeypatch: MonkeyPatch,
    feedback_value: str,
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
            "status": "success",
            "message": "Feedback kaydedildi.",
            "feedback": feedback_value,
        }

    monkeypatch.setattr(
        feedback_routes,
        "post_to_n8n",
        fake_post_to_n8n,
    )

    payload = valid_feedback_payload(feedback=feedback_value)

    response = feedback_client.post(
        "/feedback",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "Feedback kaydedildi.",
        "feedback": feedback_value,
    }

    assert captured_request["url"] == "http://testserver/feedback"
    assert captured_request["timeout_seconds"] == 5.0

    assert captured_request["payload"]["question"] == (
        "VPN bağlantısı kuramıyorum."
    )
    assert captured_request["payload"]["feedback"] == feedback_value
    assert len(captured_request["payload"]["sources"]) == 1


def test_feedback_handles_n8n_error_safely(
    feedback_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    async def fake_post_to_n8n(**_kwargs: Any) -> dict[str, Any]:
        raise N8nClientError("Internal feedback error.")

    monkeypatch.setattr(
        feedback_routes,
        "post_to_n8n",
        fake_post_to_n8n,
    )

    response = feedback_client.post(
        "/feedback",
        json=valid_feedback_payload(),
    )

    assert response.status_code == 502
    assert response.json() == {
        "detail": (
            "Geri bildirim servisine şu anda ulaşılamıyor. "
            "Lütfen daha sonra tekrar deneyin."
        ),
    }

    assert "Internal feedback error" not in response.text