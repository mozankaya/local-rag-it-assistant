from datetime import datetime
from pathlib import Path
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
    try:
        import fitz  # PyMuPDF
    except ImportError as error:
        raise RuntimeError(
            "PyMuPDF kurulu değil. Backend sanal ortamında şu komutu çalıştır: pip install pymupdf"
        ) from error

    sections = []

    with fitz.open(path) as document:
        for page_index, page in enumerate(document, start=1):
            page_text = clean_text(page.get_text("text"))

            if page_text:
                sections.append(f"## Sayfa {page_index}\n\n{page_text}")

    if not sections:
        raise RuntimeError(
            "PDF dosyasından metin çıkarılamadı. Dosya taranmış/görsel PDF olabilir veya boş olabilir."
        )

    return "\n\n".join(sections)


def extract_docx(path: Path) -> str:
    try:
        from docx import Document
    except ImportError as error:
        raise RuntimeError(
            "python-docx kurulu değil. Backend sanal ortamında şu komutu çalıştır: pip install python-docx"
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

    for table_index, table in enumerate(document.tables, start=1):
        table_lines = []

        for row in table.rows:
            cells = [clean_text(cell.text) for cell in row.cells]
            cells = [cell for cell in cells if cell]

            if cells:
                table_lines.append(" | ".join(cells))

        if table_lines:
            lines.append(f"## Tablo {table_index}")
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


def infer_category(path: Path) -> str:
    """
    data/source-documents/vpn/file.pdf gibi klasör varsa category = vpn olur.
    Direkt source-documents altındaysa general olur.
    """
    relative_parent = path.parent.relative_to(SOURCE_DIR)

    if str(relative_parent) == ".":
        return "general"

    return slugify(relative_parent.parts[0])


def clean_processed_documents_dir() -> None:
    """
    documents.json her çalışmada yeniden oluşturulduğu için eski processed .md çıktıları da temizlenir.
    Böylece silinen veya artık işlenemeyen dokümanların eski çıktıları kalmaz.
    """
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for file_path in PROCESSED_DIR.glob("*.md"):
        file_path.unlink(missing_ok=True)


def process_file(path: Path) -> dict:
    title = title_from_filename(path)
    document_id = slugify(path.stem)
    category = infer_category(path)
    content_hash = file_hash(path)

    extracted_content = clean_text(extract_content(path))

    if not extracted_content:
        raise RuntimeError("Dokümandan çıkarılan içerik boş.")

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
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
    }


def main() -> int:
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        path
        for path in SOURCE_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    clean_processed_documents_dir()

    if not files:
        MANIFEST_PATH.write_text(
            json.dumps([], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(f"No supported documents found in: {SOURCE_DIR}")
        print("Supported file types: .md, .txt, .pdf, .docx")
        print("Manifest reset to empty list.")
        return 0

    manifest = []
    document_ids = set()
    skipped_files = []

    for path in sorted(files):
        try:
            print(f"Processing: {path.relative_to(PROJECT_ROOT)}")
            processed_document = process_file(path)

            document_id = processed_document["document_id"]

            if document_id in document_ids:
                raise RuntimeError(
                    f"Aynı document_id birden fazla dosyada oluştu: {document_id}. "
                    "Lütfen dosya adlarını farklılaştır."
                )

            document_ids.add(document_id)
            manifest.append(processed_document)

        except Exception as error:
            skipped_files.append(
                {
                    "file": str(path.relative_to(PROJECT_ROOT)),
                    "error": str(error),
                }
            )

            print(
                f"Skipped: {path.relative_to(PROJECT_ROOT)} -> {error}",
                file=sys.stderr,
            )

    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Processed documents: {len(manifest)}")
    print(f"Skipped documents: {len(skipped_files)}")
    print(f"Total manifest records: {len(manifest)}")
    print(f"Manifest written to: {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")
    print(f"Processed files written to: {PROCESSED_DIR.relative_to(PROJECT_ROOT)}")

    if skipped_files:
        print()
        print("Skipped files:", file=sys.stderr)

        for skipped_file in skipped_files:
            print(
                f"- {skipped_file['file']}: {skipped_file['error']}",
                file=sys.stderr,
            )

        print()
        print(
            "Not: Atlanan dosyalar documents.json içine eklenmediği için n8n tarafından indexlenmez.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())