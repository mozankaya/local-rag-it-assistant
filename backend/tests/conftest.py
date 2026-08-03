import os
from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ["N8N_RAG_WEBHOOK_URL"] = "http://testserver/rag"
os.environ["N8N_FEEDBACK_WEBHOOK_URL"] = "http://testserver/feedback"
os.environ["N8N_REINDEX_WEBHOOK_URL"] = "http://testserver/reindex"
os.environ["N8N_WEBHOOK_SECRET"] = "test-webhook-secret"

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

os.environ["JWT_SECRET_KEY"] = "test-only-secret-key-not-for-production"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"


from app.core.config import Settings, get_settings  # noqa: E402

get_settings.cache_clear()


from app.api.routes.auth import (  # noqa: E402
    get_current_user,
    router as auth_router,
)
from app.api.routes.chat import router as chat_router  # noqa: E402
from app.api.routes.feedback import router as feedback_router  # noqa: E402
from app.db.database import get_db  # noqa: E402
from app.models.user import User  # noqa: E402


def override_get_db() -> Generator[object, None, None]:
    yield object()


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        _env_file=None,
        n8n_rag_webhook_url="http://testserver/rag",
        n8n_feedback_webhook_url="http://testserver/feedback",
        n8n_reindex_webhook_url="http://testserver/reindex",
        n8n_webhook_secret="test-webhook-secret",
        request_timeout_seconds=5,
        reindex_timeout_seconds=5,
        max_question_length=1000,
        database_url="sqlite+pysqlite:///:memory:",
        jwt_secret_key="test-only-secret-key-not-for-production",
        jwt_algorithm="HS256",
        access_token_expire_minutes=60,
    )


@pytest.fixture
def active_user() -> User:
    return User(
        id=1,
        email="user@example.com",
        full_name="Test User",
        hashed_password="fake-hashed-password",
        role="user",
        is_active=True,
    )


@pytest.fixture
def auth_client() -> Generator[TestClient, None, None]:
    auth_app = FastAPI()
    auth_app.include_router(auth_router)

    auth_app.dependency_overrides[get_db] = override_get_db

    with TestClient(auth_app) as client:
        yield client

    auth_app.dependency_overrides.clear()


@pytest.fixture
def chat_client(
    active_user: User,
    test_settings: Settings,
) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(chat_router)

    app.dependency_overrides[get_current_user] = lambda: active_user
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_chat_client(
    test_settings: Settings,
) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(chat_router)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def feedback_client(
    active_user: User,
    test_settings: Settings,
) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(feedback_router)

    app.dependency_overrides[get_current_user] = lambda: active_user
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_feedback_client(
    test_settings: Settings,
) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(feedback_router)

    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
