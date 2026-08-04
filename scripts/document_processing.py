from datetime import datetime
from pathlib import Path
import hashlib
import re


SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx"}


def slugify(value: str) -> str:
    """Convert text to a stable lowercase document ID."""

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
    """Normalize line endings, collapse horizontal whitespace, and limit consecutive blank lines."""

    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def title_from_filename(path: Path) -> str:
    title = path.stem.replace("_", " ").replace("-", " ")
    return " ".join(word.capitalize() for word in title.split())


def ensure_section_heading(text: str) -> str:
    """Add a general level-two heading when the text has no level-two headings."""

    if re.search(r"^##\s+", text, flags=re.MULTILINE):
        return text

    return f"## Genel\n\n{text}"


def extract_markdown(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(text)

    if not text:
        raise RuntimeError("Markdown dosyası boş veya okunamadı.")

    return ensure_section_heading(text)


def extract_txt(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = clean_text(text)

    if not text:
        raise RuntimeError("TXT dosyası boş veya okunamadı.")

    return ensure_section_heading(text)


def extract_pdf(path: Path) -> str:
    """Extract non-empty text into one Markdown section per PDF page."""

    try:
        import fitz  # PyMuPDF
    except ImportError as error:
        raise RuntimeError(
            "PyMuPDF kurulu değil. Backend sanal ortamında "
            "pip install pymupdf komutunu çalıştır."
        ) from error

    sections = []

    with fitz.open(path) as document:
        for page_number, page in enumerate(document, start=1):
            page_text = clean_text(page.get_text("text"))

            if page_text:
                sections.append(f"## Sayfa {page_number}\n\n{page_text}")

    if not sections:
        raise RuntimeError(
            "PDF dosyasından metin çıkarılamadı. "
            "Dosya taranmış, görsel veya boş olabilir."
        )

    return "\n\n".join(sections)


def extract_docx(path: Path) -> str:
    """Convert non-empty paragraphs and tables to Markdown-like text, preserving recognized headings."""

    try:
        from docx import Document
    except ImportError as error:
        raise RuntimeError(
            "python-docx kurulu değil. Backend sanal ortamında "
            "pip install python-docx komutunu çalıştır."
        ) from error

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

    for table_number, table in enumerate(document.tables, start=1):
        table_lines = []

        for row in table.rows:
            cells = [clean_text(cell.text) for cell in row.cells]
            cells = [cell for cell in cells if cell]

            if cells:
                table_lines.append(" | ".join(cells))

        if table_lines:
            lines.append(f"## Tablo {table_number}")
            lines.extend(table_lines)

    text = clean_text("\n\n".join(lines))

    if not text:
        raise RuntimeError("DOCX dosyasından metin çıkarılamadı.")

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

    raise ValueError(f"Desteklenmeyen dosya türü: {extension}")


def infer_category(path: Path, source_dir: Path) -> str:
    """Use the first source subdirectory as the category, or general for root files."""

    relative_parent = path.parent.relative_to(source_dir)

    if str(relative_parent) == ".":
        return "general"

    return slugify(relative_parent.parts[0])


def process_file(path: Path, output_dir: Path, source_dir: Path) -> dict:
    """Write one normalized Markdown file and return its manifest record."""

    title = title_from_filename(path)
    document_id = slugify(path.stem)
    category = infer_category(path, source_dir)
    content_hash = file_hash(path)

    extracted_content = clean_text(extract_content(path))

    if not extracted_content:
        raise RuntimeError("Dokümandan çıkarılan içerik boş.")

    processed_time = datetime.now()
    source_file_type = path.suffix.lower().replace(".", "")
    output_file_name = f"{document_id}.md"
    output_path = output_dir / output_file_name

    markdown = f"""# {title}

<!--
source_file_name: {path.name}
source_file_type: {source_file_type}
content_hash: {content_hash}
processed_at: {processed_time.isoformat(timespec="seconds")}
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
        "file_type": source_file_type,
        "content_hash": content_hash,
        "last_updated": processed_time.strftime("%Y-%m-%d"),
    }
