from pathlib import Path
from datetime import datetime
import hashlib
import json
import re
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_DIR = PROJECT_ROOT / "data" / "source-documents"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed-documents"
MANIFEST_PATH = PROJECT_ROOT / "data" / "documents.json"

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx"}


def slugify(value: str) -> str:
    value = value.lower()
    value = value.replace("ı", "i").replace("ğ", "g").replace("ü", "u")
    value = value.replace("ş", "s").replace("ö", "o").replace("ç", "c")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "document"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def title_from_filename(path: Path) -> str:
    title = path.stem.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in title.split())


def ensure_section_heading(text: str) -> str:
    """
    n8n ingestion workflow section_title üretmek için ## başlıklarını kullanıyor.
    Dosyada hiç ## başlık yoksa Genel bölümü eklenir.
    """
    if re.search(r"^##\s+", text, flags=re.MULTILINE):
        return text

    return f"## Genel\n\n{text}"


def extract_markdown(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return ensure_section_heading(text)


def extract_txt(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return ensure_section_heading(text)


def extract_pdf(path: Path) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise RuntimeError("PyMuPDF is not installed. Run: pip install pymupdf")

    sections = []

    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            page_text = clean_text(page.get_text("text"))

            if page_text:
                sections.append(f"## Sayfa {page_index}\n\n{page_text}")

    if not sections:
        return (
            "## Genel\n\n"
            "Bu PDF dosyasından metin çıkarılamadı. "
            "Dosya taranmış/görsel PDF olabilir ve OCR gerektirebilir."
        )

    return "\n\n".join(sections)


def extract_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError:
        raise RuntimeError("python-docx is not installed. Run: pip install python-docx")

    document = Document(path)
    lines = []

    for paragraph in document.paragraphs:
        text = clean_text(paragraph.text)

        if not text:
            continue

        style_name = ""
        if paragraph.style and paragraph.style.name:
            style_name = paragraph.style.name.lower()

        if "heading" in style_name or "başlık" in style_name:
            lines.append(f"## {text}")
        else:
            lines.append(text)

    for table_index, table in enumerate(document.tables, start=1):
        lines.append(f"## Tablo {table_index}")

        for row in table.rows:
            cells = [clean_text(cell.text) for cell in row.cells]
            cells = [cell for cell in cells if cell]

            if cells:
                lines.append(" | ".join(cells))

    text = "\n\n".join(lines)
    return ensure_section_heading(text)


def extract_content(path: Path) -> str:
    extension = path.suffix.lower()

    if extension == ".md":
        return extract_markdown(path)

    if extension == ".txt":
        return extract_txt(path)

    if extension == ".pdf":
        return extract_pdf(path)

    if extension == ".docx":
        return extract_docx(path)

    raise ValueError(f"Unsupported file type: {extension}")


def infer_category(path: Path) -> str:
    """
    data/source-documents/vpn/file.pdf gibi klasör varsa category = vpn olur.
    Direkt source-documents altındaysa general olur.
    """
    relative_parent = path.parent.relative_to(SOURCE_DIR)

    if str(relative_parent) == ".":
        return "general"

    return slugify(relative_parent.parts[0])


def load_existing_manifest() -> list:
    if not MANIFEST_PATH.exists():
        return []

    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        if not isinstance(manifest, list):
            print("Warning: Existing documents.json is not a list. A new manifest will be created.")
            return []

        return manifest

    except json.JSONDecodeError:
        print("Warning: Existing documents.json could not be parsed. A new manifest will be created.")
        return []


def process_file(path: Path) -> dict:
    title = title_from_filename(path)
    document_id = slugify(path.stem)
    category = infer_category(path)
    content_hash = file_hash(path)

    extracted_content = clean_text(extract_content(path))

    output_file_name = f"{document_id}.md"
    output_path = PROCESSED_DIR / output_file_name

    markdown = f"""# {title}

<!--
source_file_name: {path.name}
source_file_type: {path.suffix.lower().replace(".", "")}
content_hash: {content_hash}
processed_at: {datetime.now().isoformat(timespec="seconds")}
-->

{extracted_content}
"""

    output_path.write_text(markdown, encoding="utf-8")

    return {
        "document_id": document_id,
        "title": title,
        "category": category,
        "file_name": output_file_name,
        "file_path": f"processed-documents/{output_file_name}",
        "source_file_name": path.name,
        "file_type": path.suffix.lower().replace(".", ""),
        "content_hash": content_hash,
        "last_updated": datetime.now().strftime("%Y-%m-%d")
    }


def main() -> int:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        path for path in SOURCE_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print(f"No supported documents found in: {SOURCE_DIR}")
        print("Supported file types: .md, .txt, .pdf, .docx")
        return 0

    existing_manifest = load_existing_manifest()

    manifest_by_id = {
        document["document_id"]: document
        for document in existing_manifest
        if document.get("document_id")
    }

    processed_count = 0

    for path in sorted(files):
        try:
            print(f"Processing: {path.relative_to(PROJECT_ROOT)}")
            processed_document = process_file(path)

            # Aynı document_id varsa günceller, yoksa yeni kayıt ekler.
            manifest_by_id[processed_document["document_id"]] = processed_document
            processed_count += 1

        except Exception as error:
            print(f"Failed to process {path.name}: {error}", file=sys.stderr)

    manifest = list(manifest_by_id.values())

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print()
    print(f"Processed documents: {processed_count}")
    print(f"Total manifest records: {len(manifest)}")
    print(f"Manifest written to: {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Processed files written to: {PROCESSED_DIR.relative_to(PROJECT_ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())