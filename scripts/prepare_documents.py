from pathlib import Path
import json
import shutil
import sys

from document_processing import (
    SUPPORTED_EXTENSIONS,
    process_file,
    slugify,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

SOURCE_DIR = DATA_DIR / "source-documents"
PROCESSED_DIR = DATA_DIR / "processed-documents"
PROCESSED_STAGING_DIR = DATA_DIR / "processed-documents-staging"
PROCESSED_BACKUP_DIR = DATA_DIR / "processed-documents-backup"

MANIFEST_PATH = DATA_DIR / "documents.json"
MANIFEST_STAGING_PATH = DATA_DIR / "documents.staging.json"
MANIFEST_BACKUP_PATH = DATA_DIR / "documents.backup.json"


def remove_path(path: Path) -> None:
    """Dosya veya klasör varsa kaldırır."""

    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def find_source_files() -> list[Path]:
    """Desteklenen kaynak dokümanları bulur."""

    return sorted(
        path
        for path in SOURCE_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def find_duplicate_ids(files: list[Path]) -> dict[str, list[Path]]:
    """Aynı document_id değerini oluşturacak dosyaları bulur."""

    grouped_files: dict[str, list[Path]] = {}

    for path in files:
        document_id = slugify(path.stem)
        grouped_files.setdefault(document_id, []).append(path)

    return {
        document_id: paths
        for document_id, paths in grouped_files.items()
        if len(paths) > 1
    }


def prepare_staging_area() -> None:
    """Eski geçici dosyaları temizleyip staging klasörünü oluşturur."""

    remove_path(PROCESSED_STAGING_DIR)
    remove_path(MANIFEST_STAGING_PATH)

    PROCESSED_STAGING_DIR.mkdir(parents=True, exist_ok=True)


def promote_staging_files() -> None:
    """Başarılı staging sonuçlarını canlı dosyaların yerine geçirir."""

    remove_path(PROCESSED_BACKUP_DIR)
    remove_path(MANIFEST_BACKUP_PATH)

    # Mevcut canlı dosyaların basit bir yedeğini al.
    # Yedekleme başarısız olursa canlı dosyalara dokunulmaz.
    if PROCESSED_DIR.exists():
        shutil.copytree(PROCESSED_DIR, PROCESSED_BACKUP_DIR)

    if MANIFEST_PATH.exists():
        shutil.copy2(MANIFEST_PATH, MANIFEST_BACKUP_PATH)

    try:
        remove_path(PROCESSED_DIR)
        remove_path(MANIFEST_PATH)

        PROCESSED_STAGING_DIR.rename(PROCESSED_DIR)
        MANIFEST_STAGING_PATH.rename(MANIFEST_PATH)

    except Exception:
        # Yarım kalan yeni dosyaları kaldır.
        remove_path(PROCESSED_DIR)
        remove_path(MANIFEST_PATH)

        # Eski dosyaları geri getir.
        if PROCESSED_BACKUP_DIR.exists():
            PROCESSED_BACKUP_DIR.rename(PROCESSED_DIR)

        if MANIFEST_BACKUP_PATH.exists():
            MANIFEST_BACKUP_PATH.rename(MANIFEST_PATH)

        raise

    remove_path(PROCESSED_BACKUP_DIR)
    remove_path(MANIFEST_BACKUP_PATH)


def print_duplicate_error(duplicates: dict[str, list[Path]]) -> None:
    print(
        "Aynı document_id değerini üreten dosyalar bulundu:",
        file=sys.stderr,
    )

    for document_id, paths in duplicates.items():
        file_names = ", ".join(
            str(path.relative_to(PROJECT_ROOT))
            for path in paths
        )
        print(f"- {document_id}: {file_names}", file=sys.stderr)

    print(
        "Dosya adlarını farklılaştırıp tekrar deneyin.",
        file=sys.stderr,
    )


def main() -> int:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    files = find_source_files()

    if not files:
        print(
            f"Desteklenen doküman bulunamadı: {SOURCE_DIR}",
            file=sys.stderr,
        )
        print(
            "Mevcut processed-documents ve documents.json korundu.",
            file=sys.stderr,
        )
        return 1

    duplicates = find_duplicate_ids(files)

    if duplicates:
        print_duplicate_error(duplicates)
        return 1

    prepare_staging_area()

    manifest = []
    errors = []

    for path in files:
        relative_path = path.relative_to(PROJECT_ROOT)

        try:
            print(f"Processing: {relative_path}")

            processed_document = process_file(
                path=path,
                output_dir=PROCESSED_STAGING_DIR,
                source_dir=SOURCE_DIR,
            )
            manifest.append(processed_document)

        except Exception as error:
            errors.append((relative_path, str(error)))
            print(
                f"Failed: {relative_path} -> {error}",
                file=sys.stderr,
            )

    if errors:
        remove_path(PROCESSED_STAGING_DIR)
        remove_path(MANIFEST_STAGING_PATH)

        print(file=sys.stderr)
        print(
            "Doküman işleme başarısız oldu. "
            "Mevcut processed-documents ve documents.json korundu.",
            file=sys.stderr,
        )
        print(
            "n8n reindex işlemi başlatılmamalıdır.",
            file=sys.stderr,
        )
        return 1

    try:
        MANIFEST_STAGING_PATH.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        promote_staging_files()

    except Exception as error:
        remove_path(PROCESSED_STAGING_DIR)
        remove_path(MANIFEST_STAGING_PATH)

        print(
            f"Yeni dokümanlar canlı alana taşınamadı: {error}",
            file=sys.stderr,
        )
        print(
            "Mevcut dokümanlar korundu veya yedekten geri yüklendi.",
            file=sys.stderr,
        )
        return 1

    print()
    print(f"Processed documents: {len(manifest)}")
    print("Skipped documents: 0")
    print(f"Total manifest records: {len(manifest)}")
    print(
        "Manifest written to: "
        f"{MANIFEST_PATH.relative_to(PROJECT_ROOT)}"
    )
    print(
        "Processed files written to: "
        f"{PROCESSED_DIR.relative_to(PROJECT_ROOT)}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
