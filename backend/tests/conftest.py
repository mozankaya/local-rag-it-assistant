import os
from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


os.environ["N8N_RAG_WEBHOOK_URL"] = "http://testserver/rag"
os.environ["N8N_FEEDBACK_WEBHOOK_URL"] = "http://testserver/feedback"
os.environ["N8N_REINDEX_WEBHOOK_URL"] = "http://testserver/reindex"

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

os.environ["JWT_SECRET_KEY"] = "test-only-secret-key-not-for-production"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"


from app.core.config import get_settings  # noqa: E402


get_settings.cache_clear()


from app.api.routes.auth import router as auth_router  # noqa: E402
from app.db.database import get_db  # noqa: E402


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    auth_app = FastAPI()
    auth_app.include_router(auth_router)

    def override_get_db() -> Generator[object, None, None]:
        # Auth fonksiyonları testlerde monkeypatch ile kontrol edileceği için
        # gerçek Session nesnesine ihtiyaç bulunmuyor.
        yield object()

    auth_app.dependency_overrides[get_db] = override_get_db

    with TestClient(auth_app) as client:
        yield client

    auth_app.dependency_overrides.clear()