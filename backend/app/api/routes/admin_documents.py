import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes.users import require_admin
from app.core.config import get_settings
from app.db.database import get_db
from app.models.user import User
from app.schemas.admin_documents import (
    AdminDocumentResponse,
    DocumentCategoryResponse,
    DocumentDeleteResponse,
    DocumentUploadResponse,
    PaginatedAdminDocumentsResponse,
    ReindexResponse,
)


router = APIRouter(
    prefix="/admin/documents",
    tags=["Admin Documents"],
)


PROJECT_ROOT_DIR = Path(__file__).resolve().parents[4]
SOURCE_DOCUMENTS_DIR = PROJECT_ROOT_DIR / "data" / "source-documents"
PROCESSED_DOCUMENTS_DIR = PROJECT_ROOT_DIR / "data" / "processed-documents"
DOCUMENTS_MANIFEST_PATH = PROJECT_ROOT_DIR / "data" / "documents.json"
PREPARE_DOCUMENTS_SCRIPT = PROJECT_ROOT_DIR / "scripts" / "prepare_documents.py"

ALLOWED_UPLOAD_EXTENSIONS = {".md", ".txt", ".pdf", ".docx"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


def get_scalar_value(db: Session, query: str, params: dict | None = None) -> int:
    result = db.execute(text(query), params or {}).scalar()
    return int(result or 0)


def find_source_document_path(
    source_file_name: str,
    category: str | None = None,
) -> Path | None:
    safe_file_name = Path(source_file_name).name

    if not safe_file_name:
        return None

    source_root = SOURCE_DOCUMENTS_DIR.resolve()

    if category and category != "unknown":
        category_candidate = (source_root / category / safe_file_name).resolve()

        if category_candidate.is_file() and category_candidate.is_relative_to(source_root):
            return category_candidate

    for file_path in source_root.rglob("*"):
        if file_path.is_file() and file_path.name == safe_file_name:
            resolved_path = file_path.resolve()

            if resolved_path.is_relative_to(source_root):
                return resolved_path

    return None


def find_processed_document_path(document_id: str) -> Path | None:
    safe_document_id = slugify_text(document_id)

    if not safe_document_id:
        return None

    processed_root = PROCESSED_DOCUMENTS_DIR.resolve()
    candidate = (processed_root / f"{safe_document_id}.md").resolve()

    if candidate.is_file() and candidate.is_relative_to(processed_root):
        return candidate

    return None

def remove_empty_directory(directory_path: Path, root_directory: Path) -> None:
    resolved_directory = directory_path.resolve()
    resolved_root = root_directory.resolve()

    if resolved_directory == resolved_root:
        return

    if not resolved_directory.is_relative_to(resolved_root):
        return

    try:
        resolved_directory.rmdir()
    except OSError:
        pass


def slugify_text(value: str) -> str:
    value = value.strip().lower()

    replacements = {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
    }

    for source, target in replacements.items():
        value = value.replace(source, target)

    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")

    return value or "document"


def ensure_allowed_file(file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()

    if suffix not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Desteklenmeyen dosya türü. Sadece .md, .txt, .pdf ve .docx desteklenmektedir.",
        )

    return suffix


def load_documents_manifest() -> list[dict]:
    if not DOCUMENTS_MANIFEST_PATH.exists():
        return []

    try:
        with DOCUMENTS_MANIFEST_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="documents.json dosyası okunamadı. JSON formatı geçersiz.",
        )

    if not isinstance(data, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="documents.json beklenen liste formatında değil.",
        )

    return data


def save_documents_manifest(documents: list[dict]) -> None:
    DOCUMENTS_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    with DOCUMENTS_MANIFEST_PATH.open("w", encoding="utf-8") as file:
        json.dump(documents, file, ensure_ascii=False, indent=2)


def remove_document_from_manifest(document_id: str) -> bool:
    documents = load_documents_manifest()

    filtered_documents = [
        document
        for document in documents
        if document.get("document_id") != document_id
    ]

    changed = len(filtered_documents) != len(documents)

    if changed:
        save_documents_manifest(filtered_documents)

    return changed


def run_prepare_documents_script() -> None:
    if not PREPARE_DOCUMENTS_SCRIPT.is_file():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="prepare_documents.py scripti bulunamadı.",
        )

    result = subprocess.run(
        [sys.executable, str(PREPARE_DOCUMENTS_SCRIPT)],
        cwd=str(PROJECT_ROOT_DIR),
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Doküman ön işleme sırasında hata oluştu: {result.stderr or result.stdout}",
        )


@router.get("", response_model=PaginatedAdminDocumentsResponse)
def list_documents(
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
    category: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    search_value = search.strip() if search else None
    category_value = category.strip() if category else None

    params = {
        "limit": limit,
        "offset": offset,
        "search": search_value,
        "category": category_value,
    }

    total = get_scalar_value(
        db,
        """
        WITH documents AS (
            SELECT
                COALESCE(metadata->>'document_id', 'unknown') AS document_id,
                COALESCE(metadata->>'title', 'Başlıksız Doküman') AS title,
                COALESCE(metadata->>'category', 'unknown') AS category,
                COALESCE(metadata->>'file_type', 'unknown') AS file_type,
                COALESCE(
                    metadata->>'source_file_name',
                    metadata->>'file_name',
                    'unknown'
                ) AS source_file_name,
                MAX(metadata->>'last_updated') AS last_updated,
                COUNT(*) AS chunk_count
            FROM langchain_document_chunks
            GROUP BY
                COALESCE(metadata->>'document_id', 'unknown'),
                COALESCE(metadata->>'title', 'Başlıksız Doküman'),
                COALESCE(metadata->>'category', 'unknown'),
                COALESCE(metadata->>'file_type', 'unknown'),
                COALESCE(
                    metadata->>'source_file_name',
                    metadata->>'file_name',
                    'unknown'
                )
        )
        SELECT COUNT(*)
        FROM documents
        WHERE
            (
                CAST(:category AS text) IS NULL
                OR category = :category
            )
            AND
            (
                CAST(:search AS text) IS NULL
                OR document_id ILIKE '%' || :search || '%'
                OR title ILIKE '%' || :search || '%'
                OR category ILIKE '%' || :search || '%'
                OR source_file_name ILIKE '%' || :search || '%'
            )
        """,
        {
            "search": search_value,
            "category": category_value,
        },
    )

    rows = db.execute(
        text(
            """
            WITH documents AS (
                SELECT
                    COALESCE(metadata->>'document_id', 'unknown') AS document_id,
                    COALESCE(metadata->>'title', 'Başlıksız Doküman') AS title,
                    COALESCE(metadata->>'category', 'unknown') AS category,
                    COALESCE(metadata->>'file_type', 'unknown') AS file_type,
                    COALESCE(
                        metadata->>'source_file_name',
                        metadata->>'file_name',
                        'unknown'
                    ) AS source_file_name,
                    MAX(metadata->>'last_updated') AS last_updated,
                    COUNT(*) AS chunk_count
                FROM langchain_document_chunks
                GROUP BY
                    COALESCE(metadata->>'document_id', 'unknown'),
                    COALESCE(metadata->>'title', 'Başlıksız Doküman'),
                    COALESCE(metadata->>'category', 'unknown'),
                    COALESCE(metadata->>'file_type', 'unknown'),
                    COALESCE(
                        metadata->>'source_file_name',
                        metadata->>'file_name',
                        'unknown'
                    )
            )
            SELECT *
            FROM documents
            WHERE
                (
                    CAST(:category AS text) IS NULL
                    OR category = :category
                )
                AND
                (
                    CAST(:search AS text) IS NULL
                    OR document_id ILIKE '%' || :search || '%'
                    OR title ILIKE '%' || :search || '%'
                    OR category ILIKE '%' || :search || '%'
                    OR source_file_name ILIKE '%' || :search || '%'
                )
            ORDER BY category ASC, title ASC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    items = [
        AdminDocumentResponse(
            document_id=row["document_id"],
            title=row["title"],
            category=row["category"],
            file_type=row["file_type"],
            source_file_name=row["source_file_name"],
            last_updated=row["last_updated"],
            chunk_count=int(row["chunk_count"]),
        )
        for row in rows
    ]

    return PaginatedAdminDocumentsResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + limit < total,
    )


@router.get("/categories", response_model=list[DocumentCategoryResponse])
def list_document_categories(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    rows = db.execute(
        text(
            """
            WITH documents AS (
                SELECT DISTINCT
                    COALESCE(metadata->>'document_id', 'unknown') AS document_id,
                    COALESCE(metadata->>'category', 'unknown') AS category
                FROM langchain_document_chunks
            )
            SELECT
                category,
                COUNT(*) AS document_count
            FROM documents
            GROUP BY category
            ORDER BY category ASC
            """
        )
    ).mappings().all()

    return [
        DocumentCategoryResponse(
            category=row["category"],
            document_count=int(row["document_count"]),
        )
        for row in rows
    ]


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    row = db.execute(
        text(
            """
            SELECT
                COALESCE(
                    metadata->>'source_file_name',
                    metadata->>'file_name'
                ) AS source_file_name,
                COALESCE(metadata->>'category', 'unknown') AS category
            FROM langchain_document_chunks
            WHERE metadata->>'document_id' = :document_id
            LIMIT 1
            """
        ),
        {"document_id": document_id},
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doküman bulunamadı.",
        )

    source_file_name = row["source_file_name"]
    category = row["category"]

    if not source_file_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doküman kaynak dosya bilgisi bulunamadı.",
        )

    file_path = find_source_document_path(
        source_file_name=source_file_name,
        category=category,
    )

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orijinal doküman dosyası bulunamadı.",
        )

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream",
    )


@router.post("/upload", response_model=DocumentUploadResponse)
def upload_document(
    title: str = Form(...),
    category: str = Form(...),
    file: UploadFile = File(...),
    _current_admin: User = Depends(require_admin),
):
    clean_title = title.strip()
    clean_category = slugify_text(category)

    if not clean_title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doküman başlığı boş olamaz.",
        )

    suffix = ensure_allowed_file(file.filename or "")

    file_base_name = slugify_text(clean_title)
    target_dir = SOURCE_DOCUMENTS_DIR / clean_category
    target_dir.mkdir(parents=True, exist_ok=True)

    target_file_path = target_dir / f"{file_base_name}{suffix}"

    if target_file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu başlık ve kategoriyle aynı isimde bir doküman zaten mevcut.",
        )

    uploaded_size = 0

    try:
        with target_file_path.open("wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                uploaded_size += len(chunk)

                if uploaded_size > MAX_UPLOAD_SIZE_BYTES:
                    target_file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Dosya boyutu 10 MB sınırını aşamaz.",
                    )

                buffer.write(chunk)

    finally:
        file.file.close()

    try:
        run_prepare_documents_script()
    except HTTPException:
        target_file_path.unlink(missing_ok=True)
        raise

    return DocumentUploadResponse(
        success=True,
        message="Doküman başarıyla yüklendi ve ön işleme alındı. Vektör veritabanını güncellemek için yeniden indeksleme çalıştırılmalıdır.",
        file_name=target_file_path.name,
        category=clean_category,
        source_path=str(target_file_path.relative_to(PROJECT_ROOT_DIR)),
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    row = db.execute(
        text(
            """
            SELECT
                COALESCE(
                    metadata->>'source_file_name',
                    metadata->>'file_name'
                ) AS source_file_name,
                COALESCE(metadata->>'category', 'unknown') AS category
            FROM langchain_document_chunks
            WHERE metadata->>'document_id' = :document_id
            LIMIT 1
            """
        ),
        {"document_id": document_id},
    ).mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Silinecek doküman bulunamadı.",
        )

    source_file_name = row["source_file_name"]
    category = row["category"]

    if not source_file_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doküman kaynak dosya bilgisi bulunamadı.",
        )

    source_file_path = find_source_document_path(
        source_file_name=source_file_name,
        category=category,
    )

    processed_file_path = find_processed_document_path(document_id)

    if source_file_path:
        source_parent_dir = source_file_path.parent
        source_file_path.unlink(missing_ok=True)
        remove_empty_directory(source_parent_dir, SOURCE_DOCUMENTS_DIR)

    if processed_file_path:
        processed_file_path.unlink(missing_ok=True)

    remove_document_from_manifest(document_id)

    try:
        run_prepare_documents_script()
    except HTTPException:
        raise

    db.execute(
        text(
            """
            DELETE FROM langchain_document_chunks
            WHERE metadata->>'document_id' = :document_id
            """
        ),
        {"document_id": document_id},
    )
    db.commit()

    return DocumentDeleteResponse(
        success=True,
        message="Doküman başarıyla silindi. Kaynak dosya, işlenmiş dosya, manifest kaydı ve indeks kayıtları kaldırıldı.",
        document_id=document_id,
    )


@router.post("/reindex", response_model=ReindexResponse)
def reindex_documents(
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    run_prepare_documents_script()

    manifest = load_documents_manifest()

    if not manifest:
        db.execute(
            text(
                """
                TRUNCATE TABLE langchain_document_chunks RESTART IDENTITY
                """
            )
        )
        db.commit()

        return ReindexResponse(
            success=True,
            message="Kaynak doküman bulunmadı. Vektör indeks kayıtları temizlendi.",
        )

    app_settings = get_settings()
    webhook_url = app_settings.n8n_reindex_webhook_url
    timeout_seconds = app_settings.reindex_timeout_seconds

    if not webhook_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="N8N_REINDEX_WEBHOOK_URL tanımlı değil.",
        )

    request = Request(
        webhook_url,
        data=b"",
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            response_body = response.read().decode("utf-8", errors="ignore")

            if response.status >= 400:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"n8n reindex workflow hata döndürdü: {response_body}",
                )

    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="ignore")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"n8n reindex workflow HTTP hatası döndürdü: {error_body}",
        ) from exc

    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="n8n reindex webhook adresine ulaşılamadı.",
        ) from exc

    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Reindex işlemi zaman aşımına uğradı.",
        ) from exc

    return ReindexResponse(
        success=True,
        message="Dokümanlar için yeniden indeksleme işlemi başarıyla tamamlandı.",
    )