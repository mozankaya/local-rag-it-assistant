import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from urllib.error import URLError

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.api.routes import admin_documents as document_routes
from app.api.routes.auth import get_current_user
from app.db.database import get_db
from app.models.user import User


class FakeResult:
    def __init__(
        self,
        *,
        scalar_result: int = 0,
        rows: list[dict[str, Any]] | None = None,
        first_result: dict[str, Any] | None = None,
    ) -> None:
        self.scalar_result = scalar_result
        self.rows = rows or []
        self.first_result = first_result

    def scalar(self) -> int:
        return self.scalar_result

    def mappings(self) -> "FakeResult":
        return self

    def all(self) -> list[dict[str, Any]]:
        return self.rows

    def first(self) -> dict[str, Any] | None:
        return self.first_result


class FakeSession:
    def __init__(self, *results: FakeResult) -> None:
        self.results = list(results)
        self.execute_calls: list[dict[str, Any]] = []
        self.commit_count = 0
        self.rollback_count = 0

    def execute(
        self,
        query: Any,
        params: dict[str, Any] | None = None,
    ) -> FakeResult:
        self.execute_calls.append(
            {
                "query": str(query),
                "params": params or {},
            }
        )

        if self.results:
            return self.results.pop(0)

        return FakeResult()

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


class FakeHTTPResponse:
    status = 200

    def read(self) -> bytes:
        return b'{"success": true}'

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(
        self,
        _exc_type: Any,
        _exc_value: Any,
        _traceback: Any,
    ) -> None:
        return None


def create_user(*, role: str = "admin") -> User:
    return User(
        id=1,
        email=f"{role}@example.com",
        full_name=f"Test {role.title()}",
        hashed_password="fake-hashed-password",
        role=role,
        is_active=True,
    )


def create_client(
    *,
    current_user: User,
    fake_db: FakeSession,
) -> TestClient:
    app = FastAPI()
    app.include_router(document_routes.router)

    app.dependency_overrides[get_current_user] = lambda: current_user
    app.dependency_overrides[get_db] = lambda: fake_db

    return TestClient(app)


def configure_temporary_paths(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Path]:
    project_root = tmp_path
    source_directory = project_root / "data" / "source-documents"
    processed_directory = project_root / "data" / "processed-documents"
    manifest_path = project_root / "data" / "documents.json"
    prepare_script = project_root / "scripts" / "prepare_documents.py"
    delete_backup_directory = (
        project_root / "data" / ".document-delete-backup"
    )
    update_backup_directory = (
        project_root / "data" / ".document-update-backup"
    )

    source_directory.mkdir(parents=True)
    processed_directory.mkdir(parents=True)
    prepare_script.parent.mkdir(parents=True)
    prepare_script.write_text("# test script", encoding="utf-8")

    monkeypatch.setattr(
        document_routes,
        "PROJECT_ROOT_DIR",
        project_root,
    )
    monkeypatch.setattr(
        document_routes,
        "SOURCE_DOCUMENTS_DIR",
        source_directory,
    )
    monkeypatch.setattr(
        document_routes,
        "PROCESSED_DOCUMENTS_DIR",
        processed_directory,
    )
    monkeypatch.setattr(
        document_routes,
        "DOCUMENTS_MANIFEST_PATH",
        manifest_path,
    )
    monkeypatch.setattr(
        document_routes,
        "PREPARE_DOCUMENTS_SCRIPT",
        prepare_script,
    )
    monkeypatch.setattr(
        document_routes,
        "DELETE_BACKUP_DIR",
        delete_backup_directory,
    )
    monkeypatch.setattr(
        document_routes,
        "UPDATE_BACKUP_DIR",
        update_backup_directory,
    )

    return {
        "project_root": project_root,
        "source_directory": source_directory,
        "processed_directory": processed_directory,
        "manifest_path": manifest_path,
        "prepare_script": prepare_script,
        "delete_backup_directory": delete_backup_directory,
        "update_backup_directory": update_backup_directory,
    }


def test_normal_user_cannot_access_admin_documents() -> None:
    fake_db = FakeSession()

    with create_client(
        current_user=create_user(role="user"),
        fake_db=fake_db,
    ) as client:
        response = client.get("/admin/documents")

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Only admin users can perform this action.",
    }


def test_admin_can_list_documents() -> None:
    fake_db = FakeSession(
        FakeResult(scalar_result=3),
        FakeResult(
            rows=[
                {
                    "document_id": "vpn-guide",
                    "title": "VPN Rehberi",
                    "category": "network",
                    "file_type": "txt",
                    "source_file_name": "vpn-guide.txt",
                    "last_updated": "2026-07-28",
                    "chunk_count": 4,
                },
                {
                    "document_id": "network-guide",
                    "title": "Ağ Rehberi",
                    "category": "network",
                    "file_type": "md",
                    "source_file_name": "network-guide.md",
                    "last_updated": "2026-07-27",
                    "chunk_count": 3,
                },
            ]
        ),
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get(
            "/admin/documents",
            params={
                "limit": 2,
                "offset": 0,
                "search": " VPN ",
                "category": " network ",
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 3
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert body["has_more"] is True
    assert len(body["items"]) == 2
    assert body["items"][0]["document_id"] == "vpn-guide"
    assert body["items"][0]["chunk_count"] == 4

    assert fake_db.execute_calls[0]["params"] == {
        "search": "VPN",
        "category": "network",
    }

    assert fake_db.execute_calls[1]["params"] == {
        "limit": 2,
        "offset": 0,
        "search": "VPN",
        "category": "network",
    }


def test_admin_can_list_document_categories() -> None:
    fake_db = FakeSession(
        FakeResult(
            rows=[
                {
                    "category": "account",
                    "document_count": 3,
                },
                {
                    "category": "network",
                    "document_count": 2,
                },
            ]
        )
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get("/admin/documents/categories")

    assert response.status_code == 200
    assert response.json() == [
        {
            "category": "account",
            "document_count": 3,
        },
        {
            "category": "network",
            "document_count": 2,
        },
    ]


def test_upload_rejects_blank_title(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_temporary_paths(monkeypatch, tmp_path)

    with create_client(
        current_user=create_user(),
        fake_db=FakeSession(),
    ) as client:
        response = client.post(
            "/admin/documents/upload",
            data={
                "title": "   ",
                "category": "network",
            },
            files={
                "file": (
                    "guide.txt",
                    b"test content",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Doküman başlığı boş olamaz.",
    }


def test_upload_rejects_unsupported_extension(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_temporary_paths(monkeypatch, tmp_path)

    with create_client(
        current_user=create_user(),
        fake_db=FakeSession(),
    ) as client:
        response = client.post(
            "/admin/documents/upload",
            data={
                "title": "VPN Rehberi",
                "category": "network",
            },
            files={
                "file": (
                    "guide.exe",
                    b"test content",
                    "application/octet-stream",
                )
            },
        )

    assert response.status_code == 400
    assert response.json() == {
        "detail": (
            "Desteklenmeyen dosya türü. "
            "Sadece .md, .txt, .pdf ve .docx desteklenmektedir."
        ),
    }


def test_upload_rejects_duplicate_document(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    target_directory = paths["source_directory"] / "network"
    target_directory.mkdir()

    existing_file = target_directory / "vpn-rehberi.txt"
    existing_file.write_text("existing", encoding="utf-8")

    with create_client(
        current_user=create_user(),
        fake_db=FakeSession(),
    ) as client:
        response = client.post(
            "/admin/documents/upload",
            data={
                "title": "VPN Rehberi",
                "category": "Network",
            },
            files={
                "file": (
                    "guide.txt",
                    b"new content",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 409
    assert response.json() == {
        "detail": (
            "Bu başlık ve kategoriyle aynı isimde "
            "bir doküman zaten mevcut."
        ),
    }

    assert existing_file.read_text(encoding="utf-8") == "existing"


def test_upload_rejects_oversized_file_and_cleans_partial_file(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    monkeypatch.setattr(
        document_routes,
        "MAX_UPLOAD_SIZE_BYTES",
        5,
    )

    with create_client(
        current_user=create_user(),
        fake_db=FakeSession(),
    ) as client:
        response = client.post(
            "/admin/documents/upload",
            data={
                "title": "VPN Rehberi",
                "category": "network",
            },
            files={
                "file": (
                    "guide.txt",
                    b"123456",
                    "text/plain",
                )
            },
        )

    target_file = (
        paths["source_directory"]
        / "network"
        / "vpn-rehberi.txt"
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Dosya boyutu 10 MB sınırını aşamaz.",
    }
    assert not target_file.exists()


def test_admin_can_upload_document(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)
    prepare_calls: list[bool] = []

    monkeypatch.setattr(
        document_routes,
        "run_prepare_documents_script",
        lambda: prepare_calls.append(True),
    )

    with create_client(
        current_user=create_user(),
        fake_db=FakeSession(),
    ) as client:
        response = client.post(
            "/admin/documents/upload",
            data={
                "title": "VPN Rehberi",
                "category": "Network",
            },
            files={
                "file": (
                    "original-name.txt",
                    b"VPN test content",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["file_name"] == "vpn-rehberi.txt"
    assert body["category"] == "network"

    assert Path(body["source_path"]).as_posix() == (
        "data/source-documents/network/vpn-rehberi.txt"
    )

    uploaded_file = (
        paths["source_directory"]
        / "network"
        / "vpn-rehberi.txt"
    )

    assert uploaded_file.read_bytes() == b"VPN test content"
    assert prepare_calls == [True]


def test_upload_cleans_file_when_preprocessing_fails(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    def fail_preprocessing() -> None:
        raise HTTPException(
            status_code=500,
            detail="Test preprocessing failure.",
        )

    monkeypatch.setattr(
        document_routes,
        "run_prepare_documents_script",
        fail_preprocessing,
    )

    with create_client(
        current_user=create_user(),
        fake_db=FakeSession(),
    ) as client:
        response = client.post(
            "/admin/documents/upload",
            data={
                "title": "VPN Rehberi",
                "category": "network",
            },
            files={
                "file": (
                    "guide.txt",
                    b"VPN content",
                    "text/plain",
                )
            },
        )

    target_file = (
        paths["source_directory"]
        / "network"
        / "vpn-rehberi.txt"
    )

    assert response.status_code == 500
    assert not target_file.exists()


def test_download_does_not_access_file_outside_source_directory(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    configure_temporary_paths(monkeypatch, tmp_path)

    outside_file = tmp_path / "secret.txt"
    outside_file.write_text("secret", encoding="utf-8")

    fake_db = FakeSession(
        FakeResult(
            first_result={
                "source_file_name": "../secret.txt",
                "category": "network",
            }
        )
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.get(
            "/admin/documents/test-document/download"
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Orijinal doküman dosyası bulunamadı.",
    }
    assert outside_file.exists()


def test_admin_can_update_document(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    source_directory = paths["source_directory"] / "network"
    source_directory.mkdir()

    source_file = source_directory / "vpn-guide.txt"
    source_file.write_text("old content", encoding="utf-8")

    prepare_calls: list[bool] = []
    monkeypatch.setattr(
        document_routes,
        "run_prepare_documents_script",
        lambda: prepare_calls.append(True),
    )

    fake_db = FakeSession(
        FakeResult(
            first_result={
                "source_file_name": "vpn-guide.txt",
                "category": "network",
            }
        )
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.put(
            "/admin/documents/vpn-guide",
            files={
                "file": (
                    "vpn-guide.txt",
                    b"new content",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["document_id"] == "vpn-guide"
    assert source_file.read_bytes() == b"new content"
    assert prepare_calls == [True]
    assert not paths["update_backup_directory"].exists()


def test_update_restores_old_file_when_preprocessing_fails(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    source_directory = paths["source_directory"] / "network"
    source_directory.mkdir()

    source_file = source_directory / "vpn-guide.txt"
    source_file.write_text("old content", encoding="utf-8")

    def fail_preprocessing() -> None:
        raise HTTPException(
            status_code=500,
            detail="Test preprocessing failure.",
        )

    monkeypatch.setattr(
        document_routes,
        "run_prepare_documents_script",
        fail_preprocessing,
    )

    fake_db = FakeSession(
        FakeResult(
            first_result={
                "source_file_name": "vpn-guide.txt",
                "category": "network",
            }
        )
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.put(
            "/admin/documents/vpn-guide",
            files={
                "file": (
                    "vpn-guide.txt",
                    b"new content",
                    "text/plain",
                )
            },
        )

    assert response.status_code == 500
    assert source_file.read_text(encoding="utf-8") == "old content"
    assert not paths["update_backup_directory"].exists()


def test_update_rejects_file_type_change(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    source_directory = paths["source_directory"] / "network"
    source_directory.mkdir()

    source_file = source_directory / "vpn-guide.txt"
    source_file.write_text("old content", encoding="utf-8")

    fake_db = FakeSession(
        FakeResult(
            first_result={
                "source_file_name": "vpn-guide.txt",
                "category": "network",
            }
        )
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.put(
            "/admin/documents/vpn-guide",
            files={
                "file": (
                    "vpn-guide.md",
                    b"# New content",
                    "text/markdown",
                )
            },
        )

    assert response.status_code == 400
    assert source_file.read_text(encoding="utf-8") == "old content"


def test_admin_can_delete_document(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    source_directory = paths["source_directory"] / "network"
    source_directory.mkdir()

    source_file = source_directory / "vpn-guide.txt"
    source_file.write_text("source content", encoding="utf-8")

    processed_file = (
        paths["processed_directory"] / "vpn-guide.md"
    )
    processed_file.write_text("processed content", encoding="utf-8")

    paths["manifest_path"].write_text(
        json.dumps(
            [
                {
                    "document_id": "vpn-guide",
                    "title": "VPN Guide",
                },
                {
                    "document_id": "other-guide",
                    "title": "Other Guide",
                },
            ]
        ),
        encoding="utf-8",
    )

    def fake_prepare_documents_script(
        allow_empty: bool = False,
    ) -> None:
        # Silme endpoint'i bu seçeneği True göndermelidir.
        assert allow_empty is True

        # Gerçek prepare_documents.py çalışsaydı,
        # silinen dokümanın processed çıktısı kaldırılırdı.
        processed_file.unlink(missing_ok=True)

        documents = json.loads(
            paths["manifest_path"].read_text(encoding="utf-8")
        )
        remaining_documents = [
            document
            for document in documents
            if document.get("document_id") != "vpn-guide"
        ]
        paths["manifest_path"].write_text(
            json.dumps(
                remaining_documents,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr(
        document_routes,
        "run_prepare_documents_script",
        fake_prepare_documents_script,
    )

    fake_db = FakeSession(
        FakeResult(
            first_result={
                "source_file_name": "vpn-guide.txt",
                "category": "network",
            }
        ),
        FakeResult(),
    )

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.delete(
            "/admin/documents/vpn-guide"
        )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["document_id"] == "vpn-guide"

    assert not source_file.exists()
    assert not processed_file.exists()
    assert not source_directory.exists()
    assert not paths["delete_backup_directory"].exists()

    remaining_manifest = json.loads(
        paths["manifest_path"].read_text(encoding="utf-8")
    )

    assert remaining_manifest == [
        {
            "document_id": "other-guide",
            "title": "Other Guide",
        }
    ]

    assert fake_db.commit_count == 1
    assert any(
        "DELETE FROM langchain_document_chunks" in call["query"]
        for call in fake_db.execute_calls
    )


def test_reindex_clears_database_when_manifest_is_empty(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    paths["manifest_path"].write_text(
        "[]",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        document_routes,
        "run_prepare_documents_script",
        lambda: None,
    )

    fake_db = FakeSession(FakeResult())

    with create_client(
        current_user=create_user(),
        fake_db=fake_db,
    ) as client:
        response = client.post("/admin/documents/reindex")

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "message": (
            "Kaynak doküman bulunmadı. "
            "Vektör indeks kayıtları temizlendi."
        ),
    }

    assert fake_db.commit_count == 1
    assert "TRUNCATE TABLE" in fake_db.execute_calls[0]["query"]


def test_reindex_calls_n8n_webhook(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    paths["manifest_path"].write_text(
        json.dumps([{"document_id": "vpn-guide"}]),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        document_routes,
        "run_prepare_documents_script",
        lambda: None,
    )

    monkeypatch.setattr(
        document_routes,
        "get_settings",
        lambda: SimpleNamespace(
            n8n_reindex_webhook_url="http://n8n.test/reindex",
            reindex_timeout_seconds=15,
        ),
    )

    captured_request: dict[str, Any] = {}

    def fake_urlopen(
        request: Any,
        timeout: float,
    ) -> FakeHTTPResponse:
        captured_request["url"] = request.full_url
        captured_request["method"] = request.get_method()
        captured_request["timeout"] = timeout

        return FakeHTTPResponse()

    monkeypatch.setattr(
        document_routes,
        "urlopen",
        fake_urlopen,
    )

    with create_client(
        current_user=create_user(),
        fake_db=FakeSession(),
    ) as client:
        response = client.post("/admin/documents/reindex")

    assert response.status_code == 200
    assert response.json()["success"] is True

    assert captured_request == {
        "url": "http://n8n.test/reindex",
        "method": "POST",
        "timeout": 15,
    }


def test_reindex_handles_connection_error(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    paths["manifest_path"].write_text(
        json.dumps([{"document_id": "vpn-guide"}]),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        document_routes,
        "run_prepare_documents_script",
        lambda: None,
    )

    monkeypatch.setattr(
        document_routes,
        "get_settings",
        lambda: SimpleNamespace(
            n8n_reindex_webhook_url="http://n8n.test/reindex",
            reindex_timeout_seconds=15,
        ),
    )

    def fail_urlopen(
        _request: Any,
        timeout: float,
    ) -> Any:
        raise URLError("Connection refused.")

    monkeypatch.setattr(
        document_routes,
        "urlopen",
        fail_urlopen,
    )

    with create_client(
        current_user=create_user(),
        fake_db=FakeSession(),
    ) as client:
        response = client.post("/admin/documents/reindex")

    assert response.status_code == 502
    assert response.json() == {
        "detail": "n8n reindex webhook adresine ulaşılamadı.",
    }


def test_reindex_handles_timeout(
    monkeypatch: MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = configure_temporary_paths(monkeypatch, tmp_path)

    paths["manifest_path"].write_text(
        json.dumps([{"document_id": "vpn-guide"}]),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        document_routes,
        "run_prepare_documents_script",
        lambda: None,
    )

    monkeypatch.setattr(
        document_routes,
        "get_settings",
        lambda: SimpleNamespace(
            n8n_reindex_webhook_url="http://n8n.test/reindex",
            reindex_timeout_seconds=15,
        ),
    )

    def timeout_urlopen(
        _request: Any,
        timeout: float,
    ) -> Any:
        raise TimeoutError("Request timed out.")

    monkeypatch.setattr(
        document_routes,
        "urlopen",
        timeout_urlopen,
    )

    with create_client(
        current_user=create_user(),
        fake_db=FakeSession(),
    ) as client:
        response = client.post("/admin/documents/reindex")

    assert response.status_code == 504
    assert response.json() == {
        "detail": "Reindex işlemi zaman aşımına uğradı.",
    }