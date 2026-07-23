import type { AdminDocument } from "../../api/adminDocumentsApi";

interface DocumentsTableProps {
  documents: AdminDocument[];
}

function displayValue(value?: string | null) {
  return value?.trim() || "—";
}

function formatDate(value?: string | null) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function DocumentsTable({ documents }: DocumentsTableProps) {
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
          </tr>
        </thead>
        <tbody>
          {documents.map((document) => (
            <tr key={document.document_id}>
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
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DocumentsTable;
