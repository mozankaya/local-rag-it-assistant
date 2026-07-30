import type { AdminDocument } from "../../../api/adminDocumentsApi";
import { formatDate } from "../../../utils/formatDate";

interface DocumentsTableProps {
  documents: AdminDocument[];
  downloadingDocumentId: string;
  deletingDocumentId: string;
  updatingDocumentId: string;
  onDownload: (document: AdminDocument) => void;
  onUpdate: (document: AdminDocument) => void;
  onDelete: (document: AdminDocument) => void;
}

function displayValue(value?: string | null) {
  return value?.trim() || "—";
}

function DocumentsTable({
  documents,
  downloadingDocumentId,
  deletingDocumentId,
  updatingDocumentId,
  onDownload,
  onUpdate,
  onDelete,
}: DocumentsTableProps) {
  if (documents.length === 0) {
    return <p className="admin-empty">Doküman bulunamadı.</p>;
  }

  return (
    <div className="admin-documents-table-wrap">
      <table className="admin-documents-table">
        <thead>
          <tr>
            <th>Başlık</th>
            <th>Document ID</th>
            <th>Kategori</th>
            <th>Dosya türü</th>
            <th>Kaynak dosya adı</th>
            <th>Chunk sayısı</th>
            <th>Son güncelleme</th>
            <th>İşlemler</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((document) => {
            const isDownloading = downloadingDocumentId === document.document_id;
            const isDeleting = deletingDocumentId === document.document_id;
            const isUpdating = updatingDocumentId === document.document_id;

            return (
            <tr key={`${document.document_id}-${document.source_file_name ?? ""}`}>
              <td>
                <div className="document-title-cell">
                  <span aria-hidden="true">▤</span>
                  <strong>{document.title}</strong>
                </div>
              </td>
              <td><code>{document.document_id}</code></td>
              <td>
                <span className="document-category-badge">
                  {displayValue(document.category)}
                </span>
              </td>
              <td>
                <span className="document-type-badge">
                  {displayValue(document.file_type).toLocaleUpperCase("tr-TR")}
                </span>
              </td>
              <td className="document-source-name">
                {displayValue(document.source_file_name)}
              </td>
              <td>
                <strong className="document-chunk-count">{document.chunk_count}</strong>
              </td>
              <td className="document-date">{formatDate(document.last_updated)}</td>
              <td>
                <div className="document-row-actions">
                  <button
                    className="document-download-button"
                    type="button"
                    disabled={Boolean(downloadingDocumentId)}
                    aria-busy={isDownloading}
                    onClick={() => onDownload(document)}
                  >
                    <span aria-hidden="true">↓</span>
                    {isDownloading ? "İndiriliyor..." : "İndir"}
                  </button>
                  <button
                    className="document-update-button"
                    type="button"
                    disabled={Boolean(updatingDocumentId)}
                    aria-busy={isUpdating}
                    onClick={() => onUpdate(document)}
                  >
                    <span aria-hidden="true">↻</span>
                    {isUpdating ? "Güncelleniyor..." : "Güncelle"}
                  </button>
                  <button
                    className="document-delete-button"
                    type="button"
                    disabled={Boolean(deletingDocumentId)}
                    aria-busy={isDeleting}
                    onClick={() => onDelete(document)}
                  >
                    {isDeleting ? "Siliniyor..." : "Sil"}
                  </button>
                </div>
              </td>
            </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default DocumentsTable;
