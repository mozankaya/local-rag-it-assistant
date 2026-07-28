from collections.abc import Generator

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.routes.auth import get_current_user
from app.api.routes.users import require_admin
from app.models.user import User


def create_user(*, role: str) -> User:
    return User(
        id=1,
        email=f"{role}@example.com",
        full_name=f"Test {role.title()}",
        hashed_password="fake-hashed-password",
        role=role,
        is_active=True,
    )


def create_authorization_client(user: User) -> TestClient:
    app = FastAPI()

    @app.get("/admin-check")
    def admin_check(
        current_admin: User = Depends(require_admin),
    ) -> dict[str, str]:
        return {
            "email": current_admin.email,
            "role": current_admin.role,
        }

    app.dependency_overrides[get_current_user] = lambda: user

    return TestClient(app)


def test_normal_user_cannot_access_admin_endpoint() -> None:
    user = create_user(role="user")

    with create_authorization_client(user) as client:
        response = client.get("/admin-check")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Only admin users can perform this action.",
    }


def test_admin_user_can_access_admin_endpoint() -> None:
    admin = create_user(role="admin")

    with create_authorization_client(admin) as client:
        response = client.get("/admin-check")

    assert response.status_code == 200
    assert response.json() == {
        "email": "admin@example.com",
        "role": "admin",
    }