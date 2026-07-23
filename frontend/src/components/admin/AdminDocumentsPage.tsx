import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  AdminDocumentsApiError,
  getAdminDocuments,
  getDocumentCategories,
  type AdminDocument,
  type DocumentCategory,
} from "../../api/adminDocumentsApi";
import type { CurrentUserResponse } from "../../api/authApi";
import AdminLayout from "./AdminLayout";
import DocumentsTable from "./DocumentsTable";
import "./admin.css";

interface AdminDocumentsPageProps {
  user: CurrentUserResponse;
  onGoToDashboard: () => void;
  onGoToReviewItems: () => void;
  onGoToUsers: () => void;
  onGoToDocuments: () => void;
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
  const [error, setError] = useState("");

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
            <span className="admin-total-pill">{total} doküman</span>
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

          {isLoading ? (
            <div className="admin-loading documents-loading" role="status">
              <span />
              Dokümanlar yükleniyor...
            </div>
          ) : (
            <DocumentsTable documents={documents} />
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
    </AdminLayout>
  );
}

export default AdminDocumentsPage;
