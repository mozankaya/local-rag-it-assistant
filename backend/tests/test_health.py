from types import SimpleNamespace
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import health as health_routes
from app.api.routes.auth import get_current_user
from app.db.database import get_db


class FakeSession:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def execute(self, _query: Any) -> None:
        if self.should_fail:
            raise RuntimeError("Database connection failed.")


class FakeHTTPResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code < 400:
            return

        request = httpx.Request(
            "GET",
            "http://service.test",
        )
        response = httpx.Response(
            self.status_code,
            request=request,
        )

        raise httpx.HTTPStatusError(
            "Service returned an error.",
            request=request,
            response=response,
        )


def create_client(
    *,
    role: str = "admin",
    database_should_fail: bool = False,
) -> TestClient:
    app = FastAPI()
    app.include_router(health_routes.router)

    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        role=role,
    )
    app.dependency_overrides[get_db] = lambda: FakeSession(
        should_fail=database_should_fail,
    )

    return TestClient(app)


def configure_status_settings(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        health_routes,
        "get_settings",
        lambda: SimpleNamespace(
            n8n_health_url="http://n8n.test/healthz",
            ollama_health_url="http://ollama.test/api/tags",
            service_status_timeout_seconds=3.0,
        ),
    )


def test_health_endpoint_returns_ok() -> None:
    with create_client() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "fastapi-gateway",
    }


def test_normal_user_cannot_access_system_status() -> None:
    with create_client(role="user") as client:
        response = client.get("/admin/system-status")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Only admin users can perform this action.",
    }


def test_system_status_returns_healthy(
    monkeypatch: MonkeyPatch,
) -> None:
    configure_status_settings(monkeypatch)

    requested_urls: list[str] = []

    def fake_get(
        url: str,
        *,
        timeout: float,
    ) -> FakeHTTPResponse:
        requested_urls.append(url)
        assert timeout == 3.0

        return FakeHTTPResponse()

    monkeypatch.setattr(
        health_routes.httpx,
        "get",
        fake_get,
    )

    with create_client() as client:
        response = client.get("/admin/system-status")

    assert response.status_code == 200
    assert response.json() == {
        "overall_status": "healthy",
        "services": {
            "api": {
                "status": "healthy",
                "message": "Backend API çalışıyor.",
            },
            "database": {
                "status": "healthy",
                "message": "PostgreSQL bağlantısı başarılı.",
            },
            "n8n": {
                "status": "healthy",
                "message": "n8n servisine erişilebiliyor.",
            },
            "ollama": {
                "status": "healthy",
                "message": "Ollama servisine erişilebiliyor.",
            },
        },
    }

    assert requested_urls == [
        "http://n8n.test/healthz",
        "http://ollama.test/api/tags",
    ]


def test_system_status_is_degraded_when_n8n_is_unavailable(
    monkeypatch: MonkeyPatch,
) -> None:
    configure_status_settings(monkeypatch)

    def fake_get(
        url: str,
        *,
        timeout: float,
    ) -> FakeHTTPResponse:
        if "n8n.test" in url:
            request = httpx.Request("GET", url)
            raise httpx.ConnectError(
                "Connection failed.",
                request=request,
            )

        return FakeHTTPResponse()

    monkeypatch.setattr(
        health_routes.httpx,
        "get",
        fake_get,
    )

    with create_client() as client:
        response = client.get("/admin/system-status")

    body = response.json()

    assert response.status_code == 200
    assert body["overall_status"] == "degraded"
    assert body["services"]["n8n"] == {
        "status": "unavailable",
        "message": "n8n servisine ulaşılamadı.",
    }
    assert body["services"]["ollama"]["status"] == "healthy"


def test_system_status_is_degraded_when_database_is_unavailable(
    monkeypatch: MonkeyPatch,
) -> None:
    configure_status_settings(monkeypatch)

    monkeypatch.setattr(
        health_routes.httpx,
        "get",
        lambda url, timeout: FakeHTTPResponse(),
    )

    with create_client(
        database_should_fail=True,
    ) as client:
        response = client.get("/admin/system-status")

    body = response.json()

    assert response.status_code == 200
    assert body["overall_status"] == "degraded"
    assert body["services"]["database"] == {
        "status": "unavailable",
        "message": "PostgreSQL bağlantısı kurulamadı.",
    }
    assert body["services"]["n8n"]["status"] == "healthy"
    assert body["services"]["ollama"]["status"] == "healthy"
