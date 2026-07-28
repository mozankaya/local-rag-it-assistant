from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.health import router as health_router


health_app = FastAPI()
health_app.include_router(health_router)

client = TestClient(health_app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "fastapi-gateway",
    }