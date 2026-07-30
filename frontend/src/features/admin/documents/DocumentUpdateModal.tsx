import { useEffect, useRef, useState } from "react";
import type { FormEvent, MouseEvent } from "react";
import type { AdminDocument } from "../../../api/adminDocumentsApi";

interface DocumentUpdateModalProps {
  document: AdminDocument | null;
  isUpdating: boolean;
  error: string;
  onClose: () => void;
  onSubmit: (file: File) => Promise<boolean>;
}

const SUPPORTED_EXTENSIONS = [".md", ".txt", ".pdf", ".docx"];
const MAX_FILE_SIZE = 10 * 1024 * 1024;

function getFileName(document: AdminDocument) {
  return document.source_file_name?.split(/[\\/]/).pop()?.trim()
    || document.document_id;
}

function getExpectedExtension(document: AdminDocument) {
  const fileName = document.source_file_name?.split(/[\\/]/).pop()?.trim() ?? "";
  const dotIndex = fileName.lastIndexOf(".");
  const sourceExtension = dotIndex >= 0
    ? fileName.slice(dotIndex).toLowerCase()
    : "";

  if (SUPPORTED_EXTENSIONS.includes(sourceExtension)) return sourceExtension;

  const fileType = document.file_type?.trim().toLowerCase() ?? "";
  const normalizedFileType = fileType
    ? (fileType.startsWith(".") ? fileType : `.${fileType}`)
    : "";
  return SUPPORTED_EXTENSIONS.includes(normalizedFileType)
    ? normalizedFileType
    : "";
}

function DocumentUpdateModal({
  document,
  isUpdating,
  error,
  onClose,
  onSubmit,
}: DocumentUpdateModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!document) return;

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && !isUpdating) onClose();
    }

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [document, isUpdating, onClose]);

  if (!document) return null;

  const fileName = getFileName(document);
  const expectedExtension = getExpectedExtension(document);

  function resetForm() {
    setFile(null);
    setValidationError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function closeModal() {
    if (isUpdating) return;
    resetForm();
    onClose();
  }

  function handleBackdropClick(event: MouseEvent<HTMLDivElement>) {
    if (event.target === event.currentTarget) closeModal();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isUpdating) return;

    if (!file) {
      setValidationError("Lütfen bir dosya seçin.");
      return;
    }

    const dotIndex = file.name.lastIndexOf(".");
    const extension = dotIndex >= 0
      ? file.name.slice(dotIndex).toLowerCase()
      : "";

    if (!SUPPORTED_EXTENSIONS.includes(extension)) {
      setValidationError("Yalnızca .md, .txt, .pdf ve .docx dosyaları desteklenmektedir.");
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setValidationError("Dosya boyutu 10 MB sınırını aşamaz.");
      return;
    }
    if (expectedExtension && extension !== expectedExtension) {
      setValidationError(
        `Yeni dosyanın uzantısı mevcut dokümanla aynı olmalıdır. Beklenen uzantı: ${expectedExtension}`,
      );
      return;
    }

    setValidationError("");
    const wasSuccessful = await onSubmit(file);

    if (wasSuccessful) {
      resetForm();
      onClose();
    }
  }

  return (
    <div className="document-upload-overlay" onMouseDown={handleBackdropClick}>
      <section
        className="document-upload-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="document-update-title"
      >
        <div className="document-upload-modal-header">
          <div>
            <h2 id="document-update-title">Doküman Dosyasını Güncelle</h2>
            <p>{document.title}</p>
          </div>
          <button
            type="button"
            className="document-upload-close"
            onClick={closeModal}
            disabled={isUpdating}
            aria-label="Pencereyi kapat"
          >
            ×
          </button>
        </div>

        <form className="document-upload-form" onSubmit={handleSubmit} noValidate>
          <dl className="document-update-details">
            <div>
              <dt>Mevcut dosya</dt>
              <dd>{fileName}</dd>
            </div>
            <div>
              <dt>Mevcut uzantı</dt>
              <dd>{expectedExtension || "—"}</dd>
            </div>
          </dl>

          <div className="document-update-info">
            <span>Kabul edilen dosya türleri: .md, .txt, .pdf, .docx</span>
            <span>Maksimum dosya boyutu: 10 MB</span>
          </div>

          <label>
            <span>Yeni Dosya</span>
            <input
              ref={fileInputRef}
              type="file"
              accept=".md,.txt,.pdf,.docx"
              onChange={(event) => {
                setFile(event.target.files?.[0] ?? null);
                setValidationError("");
              }}
              disabled={isUpdating}
              autoFocus
              required
            />
          </label>

          {(validationError || error) && (
            <div className="document-upload-error" role="alert">
              {validationError || error}
            </div>
          )}

          <div className="document-upload-actions">
            <button type="button" className="document-upload-cancel" onClick={closeModal} disabled={isUpdating}>
              İptal
            </button>
            <button type="submit" className="document-upload-submit" disabled={isUpdating} aria-busy={isUpdating}>
              {isUpdating ? "Güncelleniyor..." : "Güncelle"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default DocumentUpdateModal;
