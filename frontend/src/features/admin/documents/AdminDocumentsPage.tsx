import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  AdminDocumentsApiError,
  deleteAdminDocument,
  downloadAdminDocument,
  getAdminDocuments,
  getDocumentCategories,
  reindexAdminDocuments,
  updateDocument,
  uploadAdminDocument,
  type AdminDocument,
  type DocumentCategory,
  type UploadDocumentPayload,
} from "../../../api/adminDocumentsApi";
import type { CurrentUserResponse } from "../../../api/authApi";
import { downloadBlob } from "../../../utils/downloadBlob";
import AdminLayout from "../shared/AdminLayout";
import DocumentUploadModal from "./DocumentUploadModal";
import DocumentUpdateModal from "./DocumentUpdateModal";
import DocumentsTable from "./DocumentsTable";
import "../../../components/admin/admin.css";

interface AdminDocumentsPageProps {
  user: CurrentUserResponse;
  onGoToDashboard: () => void;
  onGoToReviewItems: () => void;
  onGoToUsers: () => void;
  onGoToDocuments: () => void;
  onGoToSystemStatus: () => void;
  onGoToChat: () => void;
  onLogout: () => void;
}

const PAGE_SIZE = 10;

function AdminDocumentsPage({
  user,
  onGoToDashboard,
  onGoToReviewItems,
  onGoToUsers,
  onGoToDocuments,
  onGoToSystemStatus,
  onGoToChat,
  onLogout,
}: AdminDocumentsPageProps) {
  const [documents, setDocuments] = useState<AdminDocument[]>([]);
  const [categories, setCategories] = useState<DocumentCategory[]>([]);
  const [total, setTotal] = useState(0);
  const [nextOffset, setNextOffset] = useState(PAGE_SIZE);
  const [hasMore, setHasMore] = useState(false);
  const [searchInput, setSearchInput] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [documentToUpdate, setDocumentToUpdate] = useState<AdminDocument | null>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateError, setUpdateError] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [downloadingDocumentId, setDownloadingDocumentId] = useState("");
  const [deletingDocumentId, setDeletingDocumentId] = useState("");

  useEffect(() => {
    let isCancelled = false;

    async function loadCategories() {
      try {
        const data = await getDocumentCategories();
        if (!isCancelled) setCategories(data);
      } catch (requestError) {
        if (isCancelled) return;

        if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
          onLogout();
          return;
        }
        if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
          onGoToChat();
          return;
        }

        setError("Doküman kategorileri yüklenemedi.");
      }
    }

    void loadCategories();
    return () => {
      isCancelled = true;
    };
  }, [onGoToChat, onLogout]);

  useEffect(() => {
    let isCancelled = false;

    async function loadDocuments() {
      try {
        const data = await getAdminDocuments(
          PAGE_SIZE,
          0,
          activeSearch,
          activeCategory,
        );
        if (isCancelled) return;

        setDocuments(data.items);
        setTotal(data.total);
        setNextOffset(data.offset + PAGE_SIZE);
        setHasMore(data.has_more);
      } catch (requestError) {
        if (isCancelled) return;

        if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
          onLogout();
          return;
        }
        if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
          onGoToChat();
          return;
        }

        setError("Dokümanlar şu anda yüklenemiyor. Lütfen tekrar deneyin.");
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    }

    void loadDocuments();
    return () => {
      isCancelled = true;
    };
  }, [activeCategory, activeSearch, onGoToChat, onLogout, refreshKey]);

  function prepareForNewQuery() {
    setError("");
    setSuccess("");
    setDocuments([]);
    setTotal(0);
    setHasMore(false);
    setNextOffset(PAGE_SIZE);
    setIsLoading(true);
  }

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextSearch = searchInput.trim();
    prepareForNewQuery();

    if (nextSearch === activeSearch) {
      setRefreshKey((current) => current + 1);
    } else {
      setActiveSearch(nextSearch);
    }
  }

  function handleCategoryChange(category: string) {
    if (category === activeCategory || isLoading) return;
    prepareForNewQuery();
    setActiveCategory(category);
  }

  async function handleLoadMore() {
    if (isLoadingMore || !hasMore) return;

    setError("");
    setIsLoadingMore(true);

    try {
      const data = await getAdminDocuments(
        PAGE_SIZE,
        nextOffset,
        activeSearch,
        activeCategory,
      );
      setDocuments((current) => [...current, ...data.items]);
      setTotal(data.total);
      setNextOffset(data.offset + PAGE_SIZE);
      setHasMore(data.has_more);
    } catch (requestError) {
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
        onLogout();
        return;
      }
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
        onGoToChat();
        return;
      }

      setError("Yeni dokümanlar yüklenemedi. Lütfen tekrar deneyin.");
    } finally {
      setIsLoadingMore(false);
    }
  }

  async function handleDownload(document: AdminDocument) {
    if (downloadingDocumentId) return;

    setError("");
    setSuccess("");
    setDownloadingDocumentId(document.document_id);

    try {
      const blob = await downloadAdminDocument(document.document_id);
      const sourceName = document.source_file_name
        ?.split(/[\\/]/)
        .pop()
        ?.trim();
      const fileName = sourceName || document.document_id;
      downloadBlob(blob, fileName);

      setSuccess(`${fileName} indirme işlemi başlatıldı.`);
    } catch (requestError) {
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
        onLogout();
        return;
      }
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
        onGoToChat();
        return;
      }

      setError("Doküman indirilemedi. Lütfen tekrar deneyin.");
    } finally {
      setDownloadingDocumentId("");
    }
  }

  async function handleDelete(document: AdminDocument) {
    if (deletingDocumentId) return;

    const isConfirmed = window.confirm(
      "Bu dokümanı silmek istediğinize emin misiniz? Bu işlem kaynak dosyayı ve indeks kayıtlarını kaldıracaktır.",
    );
    if (!isConfirmed) return;

    setError("");
    setSuccess("");
    setDeletingDocumentId(document.document_id);

    try {
      await deleteAdminDocument(document.document_id);
    } catch (requestError) {
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
        setDeletingDocumentId("");
        onLogout();
        return;
      }
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
        setDeletingDocumentId("");
        onGoToChat();
        return;
      }

      const detail = requestError instanceof AdminDocumentsApiError
        ? requestError.detail
        : undefined;
      setError(detail || "Doküman silinemedi. Lütfen tekrar deneyin.");
      setDeletingDocumentId("");
      return;
    }

    setSuccess("Doküman başarıyla silindi.");
    setIsLoading(true);

    try {
      const [documentsData, categoriesData] = await Promise.all([
        getAdminDocuments(PAGE_SIZE, 0, activeSearch, activeCategory),
        getDocumentCategories(),
      ]);

      setDocuments(documentsData.items);
      setTotal(documentsData.total);
      setNextOffset(documentsData.offset + PAGE_SIZE);
      setHasMore(documentsData.has_more);
      setCategories(categoriesData);
    } catch (requestError) {
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
        onLogout();
      } else if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
        onGoToChat();
      } else {
        setError("Doküman silindi ancak listeler yenilenemedi. Lütfen tekrar deneyin.");
      }
    } finally {
      setIsLoading(false);
      setDeletingDocumentId("");
    }
  }

  async function handleReindex() {
    if (isReindexing) return;

    setError("");
    setSuccess("");
    setIsReindexing(true);

    try {
      await reindexAdminDocuments();
    } catch (requestError) {
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
        setIsReindexing(false);
        onLogout();
        return;
      }
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
        setIsReindexing(false);
        onGoToChat();
        return;
      }

      setError("Yeniden indeksleme işlemi başarısız oldu. Lütfen tekrar deneyin.");
      setIsReindexing(false);
      return;
    }

    setSuccess("Dokümanlar başarıyla yeniden indekslendi.");
    setIsLoading(true);

    try {
      const [documentsData, categoriesData] = await Promise.all([
        getAdminDocuments(PAGE_SIZE, 0, activeSearch, activeCategory),
        getDocumentCategories(),
      ]);

      setDocuments(documentsData.items);
      setTotal(documentsData.total);
      setNextOffset(documentsData.offset + PAGE_SIZE);
      setHasMore(documentsData.has_more);
      setCategories(categoriesData);
    } catch (requestError) {
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
        onLogout();
        return;
      }
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
        onGoToChat();
        return;
      }

      setError("Yeniden indeksleme tamamlandı ancak listeler yenilenemedi. Lütfen tekrar deneyin.");
    } finally {
      setIsLoading(false);
      setIsReindexing(false);
    }
  }

  function openUploadModal() {
    setUploadError("");
    setIsUploadModalOpen(true);
  }

  function closeUploadModal() {
    if (isUploading) return;
    setUploadError("");
    setIsUploadModalOpen(false);
  }

  async function handleUpload(payload: UploadDocumentPayload): Promise<boolean> {
    if (isUploading) return false;

    setError("");
    setSuccess("");
    setUploadError("");
    setIsUploading(true);

    try {
      await uploadAdminDocument(payload);
    } catch (requestError) {
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
        setIsUploading(false);
        onLogout();
        return false;
      }
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
        setIsUploading(false);
        onGoToChat();
        return false;
      }

      const detail = requestError instanceof AdminDocumentsApiError
        ? requestError.detail
        : undefined;
      setUploadError(detail || "Doküman yüklenemedi. Lütfen tekrar deneyin.");
      setIsUploading(false);
      return false;
    }

    setSuccess("Doküman başarıyla yüklendi. Değişikliklerin RAG sistemine yansıması için yeniden indeksleme çalıştırılmalıdır.");
    setIsLoading(true);

    try {
      const [documentsData, categoriesData] = await Promise.all([
        getAdminDocuments(PAGE_SIZE, 0, activeSearch, activeCategory),
        getDocumentCategories(),
      ]);

      setDocuments(documentsData.items);
      setTotal(documentsData.total);
      setNextOffset(documentsData.offset + PAGE_SIZE);
      setHasMore(documentsData.has_more);
      setCategories(categoriesData);
    } catch (requestError) {
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
        onLogout();
      } else if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
        onGoToChat();
      } else {
        setError("Doküman yüklendi ancak listeler yenilenemedi. Lütfen tekrar deneyin.");
      }
    } finally {
      setIsLoading(false);
      setIsUploading(false);
    }

    return true;
  }

  function openUpdateModal(document: AdminDocument) {
    setUpdateError("");
    setDocumentToUpdate(document);
  }

  function closeUpdateModal() {
    if (isUpdating) return;
    setUpdateError("");
    setIsUpdating(false);
    setDocumentToUpdate(null);
  }

  async function handleUpdate(file: File): Promise<boolean> {
    if (!documentToUpdate || isUpdating) return false;

    setError("");
    setSuccess("");
    setUpdateError("");
    setIsUpdating(true);

    try {
      await updateDocument(documentToUpdate.document_id, file);
    } catch (requestError) {
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
        setIsUpdating(false);
        onLogout();
        return false;
      }
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
        setIsUpdating(false);
        onGoToChat();
        return false;
      }

      const detail = requestError instanceof AdminDocumentsApiError
        ? requestError.detail
        : undefined;
      setUpdateError(detail || "Doküman güncellenemedi.");
      setIsUpdating(false);
      return false;
    }

    setSuccess("Doküman güncellendi. Değişikliklerin chatbot'a yansıması için yeniden indeksleme işlemini çalıştırın.");
    setIsLoading(true);

    try {
      const documentsData = await getAdminDocuments(
        PAGE_SIZE,
        0,
        activeSearch,
        activeCategory,
      );

      setDocuments(documentsData.items);
      setTotal(documentsData.total);
      setNextOffset(documentsData.offset + PAGE_SIZE);
      setHasMore(documentsData.has_more);
    } catch (requestError) {
      if (requestError instanceof AdminDocumentsApiError && requestError.status === 401) {
        onLogout();
      } else if (requestError instanceof AdminDocumentsApiError && requestError.status === 403) {
        onGoToChat();
      } else {
        setError("Doküman güncellendi ancak liste yenilenemedi. Lütfen tekrar deneyin.");
      }
    } finally {
      setIsLoading(false);
      setIsUpdating(false);
    }

    return true;
  }

  return (
    <AdminLayout
      user={user}
      activePage="documents"
      pageTitle="Doküman Yönetimi"
      pageDescription="RAG bilgi tabanındaki dokümanları ve kategorileri inceleyin"
      onGoToDashboard={onGoToDashboard}
      onGoToReviewItems={onGoToReviewItems}
      onGoToUsers={onGoToUsers}
      onGoToDocuments={onGoToDocuments}
      onGoToSystemStatus={onGoToSystemStatus}
      onGoToChat={onGoToChat}
      onLogout={onLogout}
    >
      <div className="admin-content admin-documents-content">
        <article className="admin-panel documents-list-panel">
          <div className="admin-panel-header documents-list-header">
            <div>
              <h2>Dokümanlar</h2>
              <p>Bilgi tabanında indekslenmiş dokümanlar</p>
            </div>
            <div className="documents-header-actions">
              <span className="admin-total-pill">{total} doküman</span>
              <button
                className="document-upload-open"
                type="button"
                onClick={openUploadModal}
                disabled={isReindexing || isUploading}
              >
                Yeni Doküman Ekle
              </button>
              <button
                className="reindex-button"
                type="button"
                onClick={handleReindex}
                disabled={isReindexing}
                aria-busy={isReindexing}
              >
                {isReindexing ? "İndeksleniyor..." : "Yeniden İndeksle"}
              </button>
            </div>
          </div>

          <form className="document-toolbar" onSubmit={handleSearch}>
            <input
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Başlık, ID, kategori veya dosya adı ara..."
              aria-label="Doküman ara"
            />
            <select
              value={activeCategory}
              onChange={(event) => handleCategoryChange(event.target.value)}
              disabled={isLoading}
              aria-label="Kategori filtresi"
            >
              <option value="">Tüm kategoriler</option>
              {categories.map((category) => (
                <option value={category.category} key={category.category}>
                  {category.category} ({category.document_count})
                </option>
              ))}
            </select>
            <button type="submit" disabled={isLoading}>Ara</button>
          </form>

          {error && <div className="admin-form-error document-list-message" role="alert">{error}</div>}
          {success && <div className="admin-success document-list-message" role="status">{success}</div>}

          {isLoading ? (
            <div className="admin-loading documents-loading" role="status">
              <span />
              Dokümanlar yükleniyor...
            </div>
          ) : (
            <DocumentsTable
              documents={documents}
              downloadingDocumentId={downloadingDocumentId}
              deletingDocumentId={deletingDocumentId}
              updatingDocumentId={documentToUpdate && isUpdating ? documentToUpdate.document_id : ""}
              onDownload={handleDownload}
              onUpdate={openUpdateModal}
              onDelete={handleDelete}
            />
          )}

          {hasMore && !isLoading && (
            <button
              className="load-more-button"
              type="button"
              onClick={handleLoadMore}
              disabled={isLoadingMore}
              aria-busy={isLoadingMore}
            >
              {isLoadingMore ? "Yükleniyor..." : "Daha fazla göster"}
            </button>
          )}
        </article>
      </div>

      <DocumentUploadModal
        isOpen={isUploadModalOpen}
        isUploading={isUploading}
        error={uploadError}
        categorySuggestions={categories.map((category) => category.category)}
        onClose={closeUploadModal}
        onSubmit={handleUpload}
      />
      <DocumentUpdateModal
        document={documentToUpdate}
        isUpdating={isUpdating}
        error={updateError}
        onClose={closeUpdateModal}
        onSubmit={handleUpdate}
      />
    </AdminLayout>
  );
}

export default AdminDocumentsPage;
