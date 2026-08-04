"""Prepare documents with staged, rollback-safe promotion of processed files and the manifest."""

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
    """Remove a file or recursively delete a directory when it exists."""

    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def find_source_files() -> list[Path]:
    return sorted(
        path
        for path in SOURCE_DIR.rglob("*")
        if (
            path.is_file()
            and path.suffix.lower() in SUPPORTED_EXTENSIONS
        )
    )


def find_duplicate_ids(
    files: list[Path],
) -> dict[str, list[Path]]:
    """Group source files whose normalized names would produce the same document ID."""

    grouped_files: dict[str, list[Path]] = {}

    for path in files:
        document_id = slugify(path.stem)

        grouped_files.setdefault(
            document_id,
            [],
        ).append(path)

    return {
        document_id: paths
        for document_id, paths in grouped_files.items()
        if len(paths) > 1
    }

def prepare_staging_area() -> None:
    """Reset staging outputs without changing live processed documents or the manifest."""

    remove_path(PROCESSED_STAGING_DIR)
    remove_path(MANIFEST_STAGING_PATH)

    PROCESSED_STAGING_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


def promote_staging_files() -> None:
    """Replace live outputs with staged files, restoring both backups if promotion fails."""

    remove_path(PROCESSED_BACKUP_DIR)
    remove_path(MANIFEST_BACKUP_PATH)

    # Back up processed documents before replacing live output.
    if PROCESSED_DIR.exists():
        shutil.copytree(
            PROCESSED_DIR,
            PROCESSED_BACKUP_DIR,
        )

    # Back up the manifest before replacing the live copy.
    if MANIFEST_PATH.exists():
        shutil.copy2(
            MANIFEST_PATH,
            MANIFEST_BACKUP_PATH,
        )

    try:
        # Remove live outputs only after staging and backups are ready.
        remove_path(PROCESSED_DIR)
        remove_path(MANIFEST_PATH)

        # Use only fully prepared staging outputs as the new live state.
        PROCESSED_STAGING_DIR.rename(
            PROCESSED_DIR
        )

        MANIFEST_STAGING_PATH.rename(
            MANIFEST_PATH
        )

    except Exception:
        # Remove partially promoted output before restoration.
        remove_path(PROCESSED_DIR)
        remove_path(MANIFEST_PATH)

        # Restore processed documents before the manifest.
        if PROCESSED_BACKUP_DIR.exists():
            PROCESSED_BACKUP_DIR.rename(
                PROCESSED_DIR
            )

        # Restore the manifest only after processed documents.
        if MANIFEST_BACKUP_PATH.exists():
            MANIFEST_BACKUP_PATH.rename(
                MANIFEST_PATH
            )

        raise

    # Remove backups only after promotion succeeds.
    remove_path(PROCESSED_BACKUP_DIR)
    remove_path(MANIFEST_BACKUP_PATH)


def print_duplicate_error(
    duplicates: dict[str, list[Path]],
) -> None:
    print(
        "Aynı document_id değerini üreten dosyalar bulundu:",
        file=sys.stderr,
    )

    for document_id, paths in duplicates.items():
        file_names = ", ".join(
            str(path.relative_to(PROJECT_ROOT))
            for path in paths
        )

        print(
            f"- {document_id}: {file_names}",
            file=sys.stderr,
        )

    print(
        "Dosya adlarını farklılaştırıp tekrar deneyin.",
        file=sys.stderr,
    )


def create_empty_document_state() -> int:
    """Create and promote empty outputs for an explicitly allowed empty-source case."""

    try:
        prepare_staging_area()

        MANIFEST_STAGING_PATH.write_text(
            json.dumps(
                [],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        promote_staging_files()

    except Exception as error:
        remove_path(PROCESSED_STAGING_DIR)
        remove_path(MANIFEST_STAGING_PATH)

        print(
            f"Boş doküman durumu oluşturulamadı: {error}",
            file=sys.stderr,
        )

        return 1

    print()
    print("Processed documents: 0")
    print("Skipped documents: 0")
    print("Total manifest records: 0")
    print(
        "Manifest written to: "
        f"{MANIFEST_PATH.relative_to(PROJECT_ROOT)}"
    )
    print(
        "Processed files written to: "
        f"{PROCESSED_DIR.relative_to(PROJECT_ROOT)}"
    )

    return 0


def main() -> int:
    """Build outputs in staging and promote them only if every source succeeds.

    Reject an empty source set unless --allow-empty is present.
    """

    SOURCE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    allow_empty = "--allow-empty" in sys.argv
    files = find_source_files()

    if not files:
        if allow_empty:
            return create_empty_document_state()

        print(
            f"Desteklenen doküman bulunamadı: {SOURCE_DIR}",
            file=sys.stderr,
        )
        print(
            "Mevcut processed-documents ve "
            "documents.json korundu.",
            file=sys.stderr,
        )

        return 1

    duplicates = find_duplicate_ids(files)

    if duplicates:
        print_duplicate_error(duplicates)
        return 1

    prepare_staging_area()

    manifest: list[dict] = []
    errors: list[tuple[Path, str]] = []

    for path in files:
        relative_path = path.relative_to(
            PROJECT_ROOT
        )

        try:
            print(
                f"Processing: {relative_path}"
            )

            processed_document = process_file(
                path=path,
                output_dir=PROCESSED_STAGING_DIR,
                source_dir=SOURCE_DIR,
            )

            manifest.append(
                processed_document
            )

        except Exception as error:
            errors.append(
                (
                    relative_path,
                    str(error),
                )
            )

            print(
                f"Failed: {relative_path} -> {error}",
                file=sys.stderr,
            )

    # Keep live outputs unchanged if any source fails.
    if errors:
        remove_path(PROCESSED_STAGING_DIR)
        remove_path(MANIFEST_STAGING_PATH)

        print(
            file=sys.stderr,
        )
        print(
            "Doküman işleme başarısız oldu.",
            file=sys.stderr,
        )
        print(
            "Mevcut processed-documents ve "
            "documents.json korundu.",
            file=sys.stderr,
        )
        print(
            "n8n reindex işlemi başlatılmamalıdır.",
            file=sys.stderr,
        )
        print(
            f"Hatalı dosya sayısı: {len(errors)}",
            file=sys.stderr,
        )

        return 1

    try:
        MANIFEST_STAGING_PATH.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        promote_staging_files()

    except Exception as error:
        remove_path(PROCESSED_STAGING_DIR)
        remove_path(MANIFEST_STAGING_PATH)

        print(
            "Yeni dokümanlar canlı alana taşınamadı: "
            f"{error}",
            file=sys.stderr,
        )
        print(
            "Mevcut dokümanlar korundu veya "
            "yedekten geri yüklendi.",
            file=sys.stderr,
        )

        return 1

    print()
    print(
        f"Processed documents: {len(manifest)}"
    )
    print("Skipped documents: 0")
    print(
        f"Total manifest records: {len(manifest)}"
    )
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