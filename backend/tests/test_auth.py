from typing import Any

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import auth as auth_routes
from app.models.user import User


def create_test_user(
    *,
    user_id: int = 1,
    email: str = "user@example.com",
    role: str = "user",
    is_active: bool = True,
) -> User:
    return User(
        id=user_id,
        email=email,
        full_name="Test User",
        hashed_password="fake-hashed-password",
        role=role,
        is_active=is_active,
    )


def test_login_returns_access_token_for_valid_credentials(
    auth_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    user = create_test_user()
    captured_email: dict[str, str] = {}

    def fake_get_user_by_email(_db: object, email: str) -> User:
        captured_email["email"] = email
        return user

    def fake_verify_password(
        plain_password: str,
        _hashed_password: str,
    ) -> bool:
        return plain_password == "Correct123!"

    def fake_create_access_token(
        subject: str,
        extra_data: dict[str, Any] | None = None,
    ) -> str:
        assert subject == "user@example.com"
        assert extra_data == {"role": "user"}

        return "test-access-token"

    monkeypatch.setattr(
        auth_routes,
        "get_user_by_email",
        fake_get_user_by_email,
    )
    monkeypatch.setattr(
        auth_routes,
        "verify_password",
        fake_verify_password,
    )
    monkeypatch.setattr(
        auth_routes,
        "create_access_token",
        fake_create_access_token,
    )

    response = auth_client.post(
        "/auth/login",
        json={
            "email": "  USER@EXAMPLE.COM  ",
            "password": "Correct123!",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "test-access-token",
        "token_type": "bearer",
    }

    assert captured_email["email"] == "user@example.com"


def test_login_rejects_unknown_user(
    auth_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        auth_routes,
        "get_user_by_email",
        lambda _db, email: None,
    )

    response = auth_client.post(
        "/auth/login",
        json={
            "email": "missing@example.com",
            "password": "Correct123!",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "E-posta veya şifre hatalı.",
    }


def test_login_rejects_wrong_password(
    auth_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    user = create_test_user()

    monkeypatch.setattr(
        auth_routes,
        "get_user_by_email",
        lambda _db, email: user,
    )
    monkeypatch.setattr(
        auth_routes,
        "verify_password",
        lambda _plain_password, _hashed_password: False,
    )

    response = auth_client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "E-posta veya şifre hatalı.",
    }


def test_login_rejects_inactive_user(
    auth_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    inactive_user = create_test_user(is_active=False)

    monkeypatch.setattr(
        auth_routes,
        "get_user_by_email",
        lambda _db, email: inactive_user,
    )
    monkeypatch.setattr(
        auth_routes,
        "verify_password",
        lambda _plain_password, _hashed_password: True,
    )

    response = auth_client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
            "password": "Correct123!",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Bu kullanıcı pasif durumda.",
    }


def test_login_requires_password(
    auth_client: TestClient,
) -> None:
    response = auth_client.post(
        "/auth/login",
        json={
            "email": "user@example.com",
        },
    )

    assert response.status_code == 422


def test_me_requires_bearer_token(
    auth_client: TestClient,
) -> None:
    response = auth_client.get("/auth/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(
    auth_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    def fake_decode_access_token(_token: str) -> dict[str, Any]:
        raise ValueError("Invalid token.")

    monkeypatch.setattr(
        auth_routes,
        "decode_access_token",
        fake_decode_access_token,
    )

    response = auth_client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Geçersiz veya süresi dolmuş token.",
    }


def test_me_returns_current_user_for_valid_token(
    auth_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    user = create_test_user()

    monkeypatch.setattr(
        auth_routes,
        "decode_access_token",
        lambda _token: {
            "sub": "user@example.com",
            "role": "user",
        },
    )
    monkeypatch.setattr(
        auth_routes,
        "get_user_by_email",
        lambda _db, email: user,
    )

    response = auth_client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer valid-test-token",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "user@example.com",
        "full_name": "Test User",
        "role": "user",
        "is_active": True,
    }


def test_me_rejects_inactive_user(
    auth_client: TestClient,
    monkeypatch: MonkeyPatch,
) -> None:
    inactive_user = create_test_user(is_active=False)

    monkeypatch.setattr(
        auth_routes,
        "decode_access_token",
        lambda _token: {
            "sub": "user@example.com",
        },
    )
    monkeypatch.setattr(
        auth_routes,
        "get_user_by_email",
        lambda _db, email: inactive_user,
    )

    response = auth_client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer valid-test-token",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Kullanıcı bulunamadı veya pasif durumda.",
    }