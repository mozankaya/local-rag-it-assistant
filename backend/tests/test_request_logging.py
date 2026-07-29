from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.request_logging import (
    REQUEST_ID_HEADER,
    RequestLoggingMiddleware,
)


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/test")
    def test_endpoint() -> dict[str, str]:
        return {
            "status": "ok",
        }

    return app


def test_request_logging_generates_request_id() -> None:
    app = create_test_app()

    with TestClient(app) as client:
        response = client.get("/test")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }

    request_id = response.headers[REQUEST_ID_HEADER]

    assert len(request_id) == 32

    # UUID hexadecimal değer olduğunu doğrular.
    int(request_id, 16)


def test_request_logging_preserves_valid_request_id() -> None:
    app = create_test_app()

    with TestClient(app) as client:
        response = client.get(
            "/test",
            headers={
                REQUEST_ID_HEADER: "frontend-request-123",
            },
        )

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == (
        "frontend-request-123"
    )


def test_request_logging_replaces_invalid_request_id() -> None:
    app = create_test_app()

    invalid_request_id = "a" * 101

    with TestClient(app) as client:
        response = client.get(
            "/test",
            headers={
                REQUEST_ID_HEADER: invalid_request_id,
            },
        )

    generated_request_id = response.headers[
        REQUEST_ID_HEADER
    ]

    assert response.status_code == 200
    assert generated_request_id != invalid_request_id
    assert len(generated_request_id) == 32