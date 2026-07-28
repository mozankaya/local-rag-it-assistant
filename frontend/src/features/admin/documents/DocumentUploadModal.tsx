import { useEffect, useRef, useState } from "react";
import type { FormEvent, MouseEvent } from "react";
import type { UploadDocumentPayload } from "../../../api/adminDocumentsApi";

interface DocumentUploadModalProps {
  isOpen: boolean;
  isUploading: boolean;
  error: string;
  categorySuggestions: string[];
  onClose: () => void;
  onSubmit: (payload: UploadDocumentPayload) => Promise<boolean>;
}

const SUPPORTED_EXTENSIONS = [".md", ".txt", ".pdf", ".docx"];

function DocumentUploadModal({
  isOpen,
  isUploading,
  error,
  categorySuggestions,
  onClose,
  onSubmit,
}: DocumentUploadModalProps) {
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!isOpen) return;

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape" && !isUploading) onClose();
    }

    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, isUploading, onClose]);

  if (!isOpen) return null;

  function resetForm() {
    setTitle("");
    setCategory("");
    setFile(null);
    setValidationError("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function closeModal() {
    if (isUploading) return;
    resetForm();
    onClose();
  }

  function handleBackdropClick(event: MouseEvent<HTMLDivElement>) {
    if (event.target === event.currentTarget) closeModal();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isUploading) return;

    const cleanTitle = title.trim();
    const cleanCategory = category.trim();

    if (!cleanTitle) {
      setValidationError("Doküman başlığı boş olamaz.");
      return;
    }
    if (!cleanCategory) {
      setValidationError("Kategori boş olamaz.");
      return;
    }
    if (!file) {
      setValidationError("Lütfen yüklenecek dosyayı seçin.");
      return;
    }

    const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!SUPPORTED_EXTENSIONS.includes(extension)) {
      setValidationError("Yalnızca .md, .txt, .pdf veya .docx dosyaları yüklenebilir.");
      return;
    }

    setValidationError("");
    const wasSuccessful = await onSubmit({
      title: cleanTitle,
      category: cleanCategory,
      file,
    });

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
        aria-labelledby="document-upload-title"
      >
        <div className="document-upload-modal-header">
          <div>
            <h2 id="document-upload-title">Yeni Doküman Ekle</h2>
            <p>RAG bilgi tabanına eklenecek kaynak dokümanı yükleyin.</p>
          </div>
          <button
            type="button"
            className="document-upload-close"
            onClick={closeModal}
            disabled={isUploading}
            aria-label="Pencereyi kapat"
          >
            ×
          </button>
        </div>

        <form className="document-upload-form" onSubmit={handleSubmit} noValidate>
          <label>
            <span>Doküman Başlığı</span>
            <input
              type="text"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              disabled={isUploading}
              autoFocus
              required
            />
          </label>

          <label>
            <span>Kategori</span>
            <input
              type="text"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              disabled={isUploading}
              list="document-category-suggestions"
              required
            />
            <datalist id="document-category-suggestions">
              {categorySuggestions.map((suggestion) => (
                <option value={suggestion} key={suggestion} />
              ))}
            </datalist>
          </label>

          <label>
            <span>Dosya</span>
            <input
              ref={fileInputRef}
              type="file"
              accept=".md,.txt,.pdf,.docx"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              disabled={isUploading}
              required
            />
            <small>Desteklenen dosyalar: .md, .txt, .pdf, .docx</small>
          </label>

          {(validationError || error) && (
            <div className="document-upload-error" role="alert">
              {validationError || error}
            </div>
          )}

          <div className="document-upload-actions">
            <button type="button" className="document-upload-cancel" onClick={closeModal} disabled={isUploading}>
              Vazgeç
            </button>
            <button type="submit" className="document-upload-submit" disabled={isUploading} aria-busy={isUploading}>
              {isUploading ? "Yükleniyor..." : "Dokümanı Yükle"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default DocumentUploadModal;
