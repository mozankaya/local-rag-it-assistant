import json
import subprocess
import sys
from pathlib import Path

from fastapi import HTTPException, status


def load_documents_manifest(
    manifest_path: Path,
) -> list[dict]:
    """Return an empty manifest when the file is missing and reject invalid manifest shapes."""

    if not manifest_path.exists():
        return []

    try:
        with manifest_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "documents.json dosyası okunamadı. "
                "JSON formatı geçersiz."
            ),
        ) from error

    if not isinstance(data, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="documents.json beklenen liste formatında değil.",
        )

    return data


def run_prepare_documents_script(
    project_root_dir: Path,
    prepare_documents_script: Path,
    allow_empty: bool = False,
) -> None:
    """Run document preparation with the current interpreter and convert subprocess failures to HTTP errors."""

    if not prepare_documents_script.is_file():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="prepare_documents.py scripti bulunamadı.",
        )

    command = [
        sys.executable,
        str(prepare_documents_script),
    ]

    if allow_empty:
        command.append("--allow-empty")

    try:
        result = subprocess.run(
            command,
            cwd=str(project_root_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )

    except subprocess.TimeoutExpired as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Doküman ön işleme işlemi zaman aşımına uğradı.",
        ) from error

    if result.returncode != 0:
        error_message = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Bilinmeyen doküman işleme hatası."
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Doküman ön işleme sırasında hata oluştu: "
                f"{error_message}"
            ),
        )