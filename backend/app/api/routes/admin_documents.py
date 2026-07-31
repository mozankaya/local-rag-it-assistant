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
    DocumentUpdateResponse,
    DocumentUploadResponse,
    PaginatedAdminDocumentsResponse,
    ReindexResponse,
)
from app.services import document_preprocessing
from app.services.document_files import (
    ensure_allowed_file,
    find_source_document_path,
    remove_empty_directory,
    save_uploaded_file,
    slugify_text,
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
DELETE_BACKUP_DIR = PROJECT_ROOT_DIR / "data" / ".document-delete-backup"
UPDATE_BACKUP_DIR = PROJECT_ROOT_DIR / "data" / ".document-update-backup"

ALLOWED_UPLOAD_EXTENSIONS = {".md", ".txt", ".pdf", ".docx"}
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


def get_scalar_value(db: Session, query: str, params: dict | None = None) -> int:
    result = db.execute(text(query), params or {}).scalar()
    return int(result or 0)

def load_documents_manifest() -> list[dict]:
    """Projenin documents.json manifest dosyasını okur."""

    return document_preprocessing.load_documents_manifest(
        manifest_path=DOCUMENTS_MANIFEST_PATH,
    )


def run_prepare_documents_script(
    allow_empty: bool = False,
) -> None:
    """Projenin doküman ön işleme scriptini çalıştırır."""

    document_preprocessing.run_prepare_documents_script(
        project_root_dir=PROJECT_ROOT_DIR,
        prepare_documents_script=PREPARE_DOCUMENTS_SCRIPT,
        allow_empty=allow_empty,
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
        source_documents_dir=SOURCE_DOCUMENTS_DIR,
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

    suffix = ensure_allowed_file(
        file_name=file.filename or "",
        allowed_extensions=ALLOWED_UPLOAD_EXTENSIONS,
    )

    file_base_name = slugify_text(clean_title)
    target_dir = SOURCE_DOCUMENTS_DIR / clean_category
    target_dir.mkdir(parents=True, exist_ok=True)

    target_file_path = target_dir / f"{file_base_name}{suffix}"

    if target_file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Bu başlık ve kategoriyle aynı isimde "
                "bir doküman zaten mevcut."
            ),
        )

    save_uploaded_file(
        file=file,
        target_path=target_file_path,
        max_upload_size_bytes=MAX_UPLOAD_SIZE_BYTES,
    )

    try:
        run_prepare_documents_script()

    except HTTPException:
        target_file_path.unlink(missing_ok=True)
        remove_empty_directory(target_dir, SOURCE_DOCUMENTS_DIR)
        raise

    return DocumentUploadResponse(
        success=True,
        message=(
            "Doküman başarıyla yüklendi ve ön işleme alındı. "
            "Vektör veritabanını güncellemek için yeniden "
            "indeksleme çalıştırılmalıdır."
        ),
        file_name=target_file_path.name,
        category=clean_category,
        source_path=str(
            target_file_path.relative_to(PROJECT_ROOT_DIR)
        ),
    )


@router.put("/{document_id}", response_model=DocumentUpdateResponse)
def update_document(
    document_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    """Mevcut dokümanın kaynak dosyasını güvenli şekilde değiştirir."""

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
            detail="Güncellenecek doküman bulunamadı.",
        )

    source_file_name = row["source_file_name"]
    category = row["category"]

    if not source_file_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doküman kaynak dosya bilgisi bulunamadı.",
        )

    source_file_path = find_source_document_path(
        source_documents_dir=SOURCE_DOCUMENTS_DIR,
        source_file_name=source_file_name,
        category=category,
    )

    if not source_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Güncellenecek kaynak doküman dosyası bulunamadı.",
        )

    new_suffix = ensure_allowed_file(
        file_name=file.filename or "",
        allowed_extensions=ALLOWED_UPLOAD_EXTENSIONS,
    )

    if new_suffix != source_file_path.suffix.lower():
        file.file.close()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Güncelleme sırasında dosya türü değiştirilemez. "
                "Aynı dosya türünü kullanın."
            ),
        )

    UPDATE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_file_path = UPDATE_BACKUP_DIR / source_file_path.name
    backup_file_path.unlink(missing_ok=True)

    # Eski dosyayı işlem tamamlanana kadar geçici klasörde tutarız.
    source_file_path.replace(backup_file_path)

    try:
        save_uploaded_file(
            file=file,
            target_path=source_file_path,
            max_upload_size_bytes=MAX_UPLOAD_SIZE_BYTES,
        )
        run_prepare_documents_script()

    except Exception:
        source_file_path.unlink(missing_ok=True)

        if backup_file_path.exists():
            backup_file_path.replace(source_file_path)

        remove_empty_directory(
            UPDATE_BACKUP_DIR,
            PROJECT_ROOT_DIR / "data",
        )
        raise

    backup_file_path.unlink(missing_ok=True)
    remove_empty_directory(
        UPDATE_BACKUP_DIR,
        PROJECT_ROOT_DIR / "data",
    )

    return DocumentUpdateResponse(
        success=True,
        message=(
            "Doküman dosyası başarıyla güncellendi ve ön işleme alındı. "
            "Vektör veritabanını güncellemek için yeniden "
            "indeksleme çalıştırılmalıdır."
        ),
        document_id=document_id,
        file_name=source_file_path.name,
        category=category,
        source_path=str(
            source_file_path.relative_to(PROJECT_ROOT_DIR)
        ),
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    _current_admin: User = Depends(require_admin),
):
    """Dokümanı güvenli şekilde siler."""

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
        source_documents_dir=SOURCE_DOCUMENTS_DIR,
        source_file_name=source_file_name,
        category=category,
    )

    if not source_file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Silinecek kaynak doküman dosyası bulunamadı.",
        )

    source_parent_dir = source_file_path.parent

    DELETE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backup_file_path = (
        DELETE_BACKUP_DIR
        / f"{document_id}{source_file_path.suffix}"
    )

    backup_file_path.unlink(missing_ok=True)

    # Dosyayı hemen silmek yerine geçici klasöre taşıyoruz.
    source_file_path.replace(backup_file_path)

    preparation_completed = False

    try:
        # Kalan kaynaklara göre processed dosyaları ve manifesti yeniler.
        # Son doküman siliniyorsa boş duruma izin verir.
        run_prepare_documents_script(allow_empty=True)
        preparation_completed = True

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

    except Exception:
        db.rollback()

        # İşlem başarısızsa kaynak dosyayı eski yerine getir.
        source_parent_dir.mkdir(parents=True, exist_ok=True)

        if backup_file_path.exists():
            backup_file_path.replace(source_file_path)

        # Script başarılı olup DB işlemi başarısız olduysa
        # processed dosyaları geri getirilen kaynağa göre yenile.
        if preparation_completed:
            try:
                run_prepare_documents_script()
            except Exception as recovery_error:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=(
                        "Doküman silinemedi. Kaynak dosya geri getirildi "
                        "ancak processed dokümanlar yeniden hazırlanamadı: "
                        f"{recovery_error}"
                    ),
                ) from recovery_error

        raise

    # Her şey başarılıysa geçici yedeğe artık gerek yok.
    backup_file_path.unlink(missing_ok=True)

    remove_empty_directory(
        source_parent_dir,
        SOURCE_DOCUMENTS_DIR,
    )
    remove_empty_directory(
        DELETE_BACKUP_DIR,
        PROJECT_ROOT_DIR / "data",
    )

    return DocumentDeleteResponse(
        success=True,
        message=(
            "Doküman başarıyla silindi. Kaynak dosya, "
            "işlenmiş dosya, manifest kaydı ve indeks "
            "kayıtları kaldırıldı."
        ),
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