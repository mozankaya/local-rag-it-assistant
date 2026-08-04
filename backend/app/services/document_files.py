from pathlib import Path

from fastapi import HTTPException, UploadFile, status


def find_source_document_path(
    source_documents_dir: Path,
    source_file_name: str,
    category: str | None = None,
) -> Path | None:
    """Find a source document by basename without allowing paths outside the source root."""

    safe_file_name = Path(source_file_name).name

    if not safe_file_name:
        return None

    source_root = source_documents_dir.resolve()

    # Use category metadata first while still enforcing source-root containment.
    if category and category != "unknown":
        category_candidate = (
            source_root / category / safe_file_name
        ).resolve()

        if (
            category_candidate.is_file()
            and category_candidate.is_relative_to(source_root)
        ):
            return category_candidate

    # Search the full source tree when category metadata is missing or stale.
    for file_path in source_root.rglob("*"):
        if file_path.is_file() and file_path.name == safe_file_name:
            resolved_path = file_path.resolve()

            if resolved_path.is_relative_to(source_root):
                return resolved_path

    return None


def remove_empty_directory(
    directory_path: Path,
    root_directory: Path,
) -> None:
    """Remove a directory only when it is empty and contained by the allowed root."""

    resolved_directory = directory_path.resolve()
    resolved_root = root_directory.resolve()

    if resolved_directory == resolved_root:
        return

    if not resolved_directory.is_relative_to(resolved_root):
        return

    try:
        resolved_directory.rmdir()
    except OSError:
        # Ignore removal failures because this cleanup is best-effort.
        pass


def slugify_text(value: str) -> str:
    import re

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


def ensure_allowed_file(
    file_name: str,
    allowed_extensions: set[str],
) -> str:
    suffix = Path(file_name).suffix.lower()

    if suffix not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Desteklenmeyen dosya türü. "
                "Sadece .md, .txt, .pdf ve .docx desteklenmektedir."
            ),
        )

    return suffix


def save_uploaded_file(
    file: UploadFile,
    target_path: Path,
    max_upload_size_bytes: int,
) -> None:
    """Stream an upload within the size limit, deleting partial output and closing the input on failure."""

    uploaded_size = 0

    try:
        with target_path.open("wb") as buffer:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                uploaded_size += len(chunk)

                if uploaded_size > max_upload_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Dosya boyutu 10 MB sınırını aşamaz.",
                    )

                buffer.write(chunk)

    except Exception:
        # Remove partial output if the upload fails.
        target_path.unlink(missing_ok=True)
        raise

    finally:
        file.file.close()