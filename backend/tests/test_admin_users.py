from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import admin_users as admin_users_routes
from app.api.routes import users as users_routes
from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.models.user import User


class FakeQuery:
    def __init__(
        self,
        *,
        first_result: Any = None,
        count_result: int = 0,
        all_result: list[Any] | None = None,
    ) -> None:
        self.first_result = first_result
        self.count_result = count_result
        self.all_result = all_result or []

        self.offset_value: int | None = None
        self.limit_value: int | None = None
        self.filter_calls: list[tuple[Any, ...]] = []

    def filter(
        self,
        *args: Any,
        **_kwargs: Any,
    ) -> "FakeQuery":
        self.filter_calls.append(args)
        return self

    def order_by(self, *_args: Any, **_kwargs: Any) -> "FakeQuery":
        return self

    def offset(self, value: int) -> "FakeQuery":
        self.offset_value = value
        return self

    def limit(self, value: int) -> "FakeQuery":
        self.limit_value = value
        return self

    def first(self) -> Any:
        return self.first_result

    def count(self) -> int:
        return self.count_result

    def all(self) -> list[Any]:
        return self.all_result


class FakeSession:
    def __init__(self, *queries: FakeQuery) -> None:
        self.queries = list(queries)
        self.added_objects: list[Any] = []
        self.commit_count = 0
        self.refreshed_objects: list[Any] = []
        self.deleted_objects: list[Any] = []

    def query(self, _model: Any) -> FakeQuery:
        if not self.queries:
            raise AssertionError("Beklenmeyen db.query çağrısı yapıldı.")

        return self.queries.pop(0)

    def add(self, value: Any) -> None:
        self.added_objects.append(value)

    def delete(self, value: Any) -> None:
        self.deleted_objects.append(value)

    def commit(self) -> None:
        self.commit_count += 1

    def refresh(self, value: Any) -> None:
        if value.id is None:
            value.id = 99

        self.refreshed_objects.append(value)


def create_user(
    *,
    user_id: int,
    email: str,
    role: str = "user",
    is_active: bool = True,
    deactivated_at: datetime | None = None,
) -> User:
    return User(
        id=user_id,
        email=email,
        full_name=f"Test User {user_id}",
        hashed_password="fake-hashed-password",
        role=role,
        is_active=is_active,
        deactivated_at=deactivated_at,
    )


def create_client(
    *,
    current_user: User,
    fake_db: FakeSession,
) -> TestClient:
    app = FastAPI()

    app.include_router(users_routes.router)
    app.include_router(admin_users_routes.router)

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_db] = lambda: fake_db

    return TestClient(app)


def test_normal_user_cannot_access_admin_users() -> None:
    normal_user = create_user(
        user_id=1,
        email="user@example.com",
        role="user",
    )
    fake_db = FakeSession()

    with create_client(
        current_user=normal_user,
        fake_db=fake_db,
    ) as client:
        response = client.get("/admin/users")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Only admin users can perform this action.",
    }


def test_admin_can_list_users() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )
    first_user = create_user(
        user_id=2,
        email="first@example.com",
    )
    second_user = create_user(
        user_id=3,
        email="second@example.com",
    )

    users_query = FakeQuery(
        count_result=3,
        all_result=[
            first_user,
            second_user,
        ],
    )
    fake_db = FakeSession(users_query)

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.get(
            "/admin/users",
            params={
                "limit": 2,
                "offset": 0,
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": 2,
                "email": "first@example.com",
                "full_name": "Test User 2",
                "role": "user",
                "is_active": True,
                "deactivated_at": None,
                "created_at": None,
            },
            {
                "id": 3,
                "email": "second@example.com",
                "full_name": "Test User 3",
                "role": "user",
                "is_active": True,
                "deactivated_at": None,
                "created_at": None,
            },
        ],
        "total": 3,
        "limit": 2,
        "offset": 0,
        "has_more": True,
    }

    assert users_query.offset_value == 0
    assert users_query.limit_value == 2


def test_admin_can_create_user(
    monkeypatch: MonkeyPatch,
) -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )

    existing_user_query = FakeQuery(first_result=None)
    fake_db = FakeSession(existing_user_query)

    monkeypatch.setattr(
        users_routes,
        "get_password_hash",
        lambda password: f"hashed::{password}",
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.post(
            "/users",
            json={
                "email": "  NEW.USER@EXAMPLE.COM  ",
                "full_name": "New User",
                "password": "Password123!",
                "role": "user",
            },
        )

    assert response.status_code == 201
    assert response.json() == {
        "id": 99,
        "email": "new.user@example.com",
        "full_name": "New User",
        "role": "user",
        "is_active": True,
    }

    assert len(fake_db.added_objects) == 1

    created_user = fake_db.added_objects[0]

    assert created_user.email == "new.user@example.com"
    assert created_user.hashed_password == "hashed::Password123!"
    assert fake_db.commit_count == 1


def test_create_user_rejects_duplicate_email() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )
    existing_user = create_user(
        user_id=2,
        email="existing@example.com",
    )

    fake_db = FakeSession(
        FakeQuery(first_result=existing_user),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.post(
            "/users",
            json={
                "email": "existing@example.com",
                "full_name": "Existing User",
                "password": "Password123!",
                "role": "user",
            },
        )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A user with this email already exists.",
    }

    assert fake_db.added_objects == []
    assert fake_db.commit_count == 0


def test_admin_can_update_user_role() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )
    target_user = create_user(
        user_id=2,
        email="target@example.com",
        role="user",
    )

    fake_db = FakeSession(
        FakeQuery(first_result=target_user),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/2/role",
            json={
                "role": "admin",
            },
        )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    assert target_user.role == "admin"
    assert fake_db.commit_count == 1


def test_update_role_rejects_invalid_role() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )
    fake_db = FakeSession()

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/2/role",
            json={
                "role": "superadmin",
            },
        )

    assert response.status_code == 422


def test_update_role_returns_404_for_unknown_user() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )

    fake_db = FakeSession(
        FakeQuery(first_result=None),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/404/role",
            json={
                "role": "admin",
            },
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Kullanıcı bulunamadı.",
    }


def test_last_active_admin_cannot_be_demoted() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
        is_active=True,
    )

    user_query = FakeQuery(first_result=admin)
    active_admin_count_query = FakeQuery(count_result=1)

    fake_db = FakeSession(
        user_query,
        active_admin_count_query,
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/1/role",
            json={
                "role": "user",
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": ("Sistemde en az bir aktif admin " "kullanıcı bulunmalıdır."),
    }

    assert admin.role == "admin"
    assert fake_db.commit_count == 0

    assert len(active_admin_count_query.filter_calls) == 1

    filter_text = " ".join(
        str(expression) for expression in active_admin_count_query.filter_calls[0]
    )

    assert "users.role" in filter_text
    assert "users.is_active" in filter_text


def test_admin_can_update_user_status(monkeypatch: MonkeyPatch) -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )
    target_user = create_user(
        user_id=2,
        email="target@example.com",
        is_active=True,
    )

    fixed_time = datetime(2026, 8, 4, 12, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(
        admin_users_routes,
        "utc_now",
        lambda: fixed_time,
    )

    fake_db = FakeSession(
        FakeQuery(first_result=target_user),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/2/status",
            json={
                "is_active": False,
            },
        )

    assert response.status_code == 200
    assert response.json()["is_active"] is False
    assert target_user.is_active is False
    assert fake_db.commit_count == 1
    assert target_user.deactivated_at == fixed_time
    assert response.json()["deactivated_at"] is not None


def test_admin_cannot_deactivate_own_account() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )

    fake_db = FakeSession(
        FakeQuery(first_result=admin),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/1/status",
            json={
                "is_active": False,
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Admin kendi hesabını pasif hale getiremez.",
    }

    assert admin.is_active is True
    assert fake_db.commit_count == 0


def test_active_admin_can_be_demoted_when_another_active_admin_exists() -> None:
    current_admin = create_user(
        user_id=1,
        email="current.admin@example.com",
        role="admin",
        is_active=True,
    )

    target_admin = create_user(
        user_id=2,
        email="target.admin@example.com",
        role="admin",
        is_active=True,
    )

    user_query = FakeQuery(first_result=target_admin)
    active_admin_count_query = FakeQuery(count_result=2)

    fake_db = FakeSession(
        user_query,
        active_admin_count_query,
    )

    with create_client(
        current_user=current_admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/2/role",
            json={
                "role": "user",
            },
        )

    assert response.status_code == 200
    assert response.json()["role"] == "user"

    assert target_admin.role == "user"
    assert fake_db.commit_count == 1


def test_inactive_admin_can_be_demoted_without_active_admin_count() -> None:
    current_admin = create_user(
        user_id=1,
        email="current.admin@example.com",
        role="admin",
        is_active=True,
    )

    inactive_admin = create_user(
        user_id=2,
        email="inactive.admin@example.com",
        role="admin",
        is_active=False,
    )

    fake_db = FakeSession(
        FakeQuery(first_result=inactive_admin),
    )

    with create_client(
        current_user=current_admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/2/role",
            json={
                "role": "user",
            },
        )

    assert response.status_code == 200
    assert response.json()["role"] == "user"

    assert inactive_admin.role == "user"
    assert fake_db.commit_count == 1


def test_repeated_deactivation_preserves_original_timestamp(
    monkeypatch: MonkeyPatch,
) -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )

    original_time = datetime(
        2026,
        7,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    inactive_user = create_user(
        user_id=2,
        email="inactive@example.com",
        is_active=False,
        deactivated_at=original_time,
    )

    monkeypatch.setattr(
        admin_users_routes,
        "utc_now",
        lambda: datetime(
            2026,
            8,
            4,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    fake_db = FakeSession(
        FakeQuery(first_result=inactive_user),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/2/status",
            json={"is_active": False},
        )

    assert response.status_code == 200
    assert inactive_user.is_active is False
    assert inactive_user.deactivated_at == original_time
    assert fake_db.commit_count == 1


def test_reactivation_clears_deactivation_timestamp() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )

    inactive_user = create_user(
        user_id=2,
        email="inactive@example.com",
        is_active=False,
        deactivated_at=datetime(
            2026,
            7,
            1,
            10,
            0,
            tzinfo=timezone.utc,
        ),
    )

    fake_db = FakeSession(
        FakeQuery(first_result=inactive_user),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/2/status",
            json={"is_active": True},
        )

    assert response.status_code == 200
    assert inactive_user.is_active is True
    assert inactive_user.deactivated_at is None
    assert response.json()["deactivated_at"] is None
    assert fake_db.commit_count == 1


def test_last_active_admin_cannot_be_deactivated() -> None:
    current_admin = create_user(
        user_id=1,
        email="current.admin@example.com",
        role="admin",
        is_active=True,
    )

    target_admin = create_user(
        user_id=2,
        email="target.admin@example.com",
        role="admin",
        is_active=True,
    )

    fake_db = FakeSession(
        FakeQuery(first_result=target_admin),
        FakeQuery(count_result=1),
    )

    with create_client(
        current_user=current_admin,
        fake_db=fake_db,
    ) as client:
        response = client.patch(
            "/admin/users/2/status",
            json={"is_active": False},
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Sistemde en az bir aktif admin kullanıcı bulunmalıdır.",
    }

    assert target_admin.is_active is True
    assert target_admin.deactivated_at is None
    assert fake_db.commit_count == 0


def test_active_user_cannot_be_permanently_deleted() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )

    active_user = create_user(
        user_id=2,
        email="active@example.com",
        is_active=True,
    )

    fake_db = FakeSession(
        FakeQuery(first_result=active_user),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.delete("/admin/users/2")

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Aktif kullanıcı kalıcı olarak silinemez. "
            "Önce kullanıcıyı pasif hale getirin."
        ),
    }

    assert fake_db.deleted_objects == []
    assert fake_db.commit_count == 0


def test_inactive_user_cannot_be_deleted_before_retention_period(
    monkeypatch: MonkeyPatch,
) -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )

    deactivated_at = datetime(
        2026,
        7,
        20,
        12,
        0,
        tzinfo=timezone.utc,
    )

    inactive_user = create_user(
        user_id=2,
        email="inactive@example.com",
        is_active=False,
        deactivated_at=deactivated_at,
    )

    monkeypatch.setattr(
        admin_users_routes,
        "utc_now",
        lambda: datetime(
            2026,
            8,
            4,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    fake_db = FakeSession(
        FakeQuery(first_result=inactive_user),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.delete("/admin/users/2")

    assert response.status_code == 409
    assert response.json() == {
        "detail": ("Bu kullanıcı için 30 günlük bekleme " "süresi henüz dolmadı."),
    }

    assert fake_db.deleted_objects == []
    assert fake_db.commit_count == 0


def test_inactive_user_can_be_deleted_after_retention_period(
    monkeypatch: MonkeyPatch,
) -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )

    deactivated_at = datetime(
        2026,
        7,
        5,
        12,
        0,
        tzinfo=timezone.utc,
    )

    inactive_user = create_user(
        user_id=2,
        email="inactive@example.com",
        is_active=False,
        deactivated_at=deactivated_at,
    )

    monkeypatch.setattr(
        admin_users_routes,
        "utc_now",
        lambda: datetime(
            2026,
            8,
            4,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    fake_db = FakeSession(
        FakeQuery(first_result=inactive_user),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.delete("/admin/users/2")

    assert response.status_code == 204
    assert response.content == b""

    assert fake_db.deleted_objects == [inactive_user]
    assert fake_db.commit_count == 1


def test_inactive_user_without_deactivation_timestamp_cannot_be_deleted() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )

    inactive_user = create_user(
        user_id=2,
        email="inactive@example.com",
        is_active=False,
        deactivated_at=None,
    )

    fake_db = FakeSession(
        FakeQuery(first_result=inactive_user),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.delete("/admin/users/2")

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Kullanıcının pasifleştirilme tarihi bulunamadı.",
    }

    assert fake_db.deleted_objects == []
    assert fake_db.commit_count == 0


def test_admin_cannot_permanently_delete_own_account() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
        is_active=False,
        deactivated_at=datetime(
            2026,
            6,
            1,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    fake_db = FakeSession(
        FakeQuery(first_result=admin),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.delete("/admin/users/1")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Admin kendi hesabını kalıcı olarak silemez.",
    }

    assert fake_db.deleted_objects == []
    assert fake_db.commit_count == 0


def test_permanent_delete_returns_404_for_unknown_user() -> None:
    admin = create_user(
        user_id=1,
        email="admin@example.com",
        role="admin",
    )

    fake_db = FakeSession(
        FakeQuery(first_result=None),
    )

    with create_client(
        current_user=admin,
        fake_db=fake_db,
    ) as client:
        response = client.delete("/admin/users/404")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Kullanıcı bulunamadı.",
    }

    assert fake_db.deleted_objects == []
    assert fake_db.commit_count == 0
