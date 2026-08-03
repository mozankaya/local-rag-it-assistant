from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import feedback as feedback_routes
from app.services.n8n_client import N8nClientError


def valid_feedback_payload(
    feedback: str = "useful",
    chat_log_id: int = 42,
) -> dict[str, Any]:
    return {
        "chat_log_id": chat_log_id,
        "feedback": feedback,
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
        json=valid_feedback_payload(
            feedback="maybe",
        ),
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid_chat_log_id",
    [
        0,
        -1,
    ],
)
def test_feedback_rejects_invalid_chat_log_id(
    feedback_client: TestClient,
    invalid_chat_log_id: int,
) -> None:
    response = feedback_client.post(
        "/feedback",
        json=valid_feedback_payload(
            chat_log_id=invalid_chat_log_id,
        ),
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
        webhook_secret: str,
    ) -> dict[str, Any]:
        captured_request["url"] = url
        captured_request["payload"] = payload
        captured_request["timeout_seconds"] = timeout_seconds
        captured_request["webhook_secret"] = webhook_secret

        return {
            "status": "success",
            "message": "Feedback kaydedildi.",
            "feedback": feedback_value,
            "chat_log_id": 42,
        }

    monkeypatch.setattr(
        feedback_routes,
        "post_to_n8n",
        fake_post_to_n8n,
    )

    payload = valid_feedback_payload(
        feedback=feedback_value,
    )

    response = feedback_client.post(
        "/feedback",
        json=payload,
    )

    assert response.status_code == 200

    assert response.json() == {
        "status": "success",
        "message": "Feedback kaydedildi.",
        "feedback": feedback_value,
        "chat_log_id": 42,
    }

    assert captured_request == {
        "url": "http://testserver/feedback",
        "payload": {
            "chat_log_id": 42,
            "feedback": feedback_value,
        },
        "timeout_seconds": 5.0,
        "webhook_secret": "test-webhook-secret",
    }


def test_feedback_returns_not_found_for_missing_chat_log(
    feedback_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    async def fake_post_to_n8n(
        **_kwargs: Any,
    ) -> dict[str, Any]:
        return {
            "status": "not_found",
            "message": "Chat log not found.",
        }

    monkeypatch.setattr(
        feedback_routes,
        "post_to_n8n",
        fake_post_to_n8n,
    )

    response = feedback_client.post(
        "/feedback",
        json=valid_feedback_payload(),
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": ("Geri bildirim gönderilecek " "sohbet kaydı bulunamadı."),
    }


def test_feedback_rejects_invalid_service_status(
    feedback_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    async def fake_post_to_n8n(
        **_kwargs: Any,
    ) -> dict[str, Any]:
        return {
            "status": "unexpected",
        }

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
        "detail": ("Geri bildirim servisinden " "geçerli bir sonuç alınamadı."),
    }


@pytest.mark.parametrize(
    "invalid_chat_log_id",
    [
        True,
        0,
        -1,
        "invalid",
    ],
)
def test_feedback_rejects_invalid_response_chat_log_id(
    feedback_client: TestClient,
    monkeypatch: MonkeyPatch,
    invalid_chat_log_id: Any,
) -> None:
    async def fake_post_to_n8n(
        **_kwargs: Any,
    ) -> dict[str, Any]:
        return {
            "status": "success",
            "message": "Feedback kaydedildi.",
            "feedback": "useful",
            "chat_log_id": invalid_chat_log_id,
        }

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
            "Geri bildirim servisinden geçerli " "bir sohbet kimliği alınamadı."
        ),
    }


def test_feedback_handles_n8n_error_safely(
    feedback_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    async def fake_post_to_n8n(
        **_kwargs: Any,
    ) -> dict[str, Any]:
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
            "Geri bildirim servisine şu anda "
            "ulaşılamıyor. Lütfen daha sonra "
            "tekrar deneyin."
        ),
    }

    assert "Internal feedback error." not in response.text
