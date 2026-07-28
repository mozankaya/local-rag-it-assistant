import { useEffect, useState } from "react";
import {
  AdminApiError,
  getReviewItems,
  type ReviewItem,
} from "../../../api/adminApi";
import type { CurrentUserResponse } from "../../../api/authApi";
import AdminLayout from "../shared/AdminLayout";
import ReviewItemsList, { type ReviewFilter } from "./ReviewItemsList";
import "../../../components/admin/admin.css";

interface AdminReviewItemsPageProps {
  user: CurrentUserResponse;
  onGoToDashboard: () => void;
  onGoToReviewItems: () => void;
  onGoToUsers: () => void;
  onGoToDocuments: () => void;
  onGoToChat: () => void;
  onLogout: () => void;
}

function isReviewableItem(item: ReviewItem) {
  return item.review_reason !== "useful"
    && item.feedback !== "useful"
    && item.response_type !== "rag_answer";
}

const PAGE_SIZE = 10;

function AdminReviewItemsPage({
  user,
  onGoToDashboard,
  onGoToReviewItems,
  onGoToUsers,
  onGoToDocuments,
  onGoToChat,
  onLogout,
}: AdminReviewItemsPageProps) {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [total, setTotal] = useState(0);
  const [nextOffset, setNextOffset] = useState(PAGE_SIZE);
  const [hasMore, setHasMore] = useState(false);
  const [activeFilter, setActiveFilter] = useState<ReviewFilter>("all");
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let isCancelled = false;

    async function loadReviewItems() {
      try {
        const reviewReason = activeFilter === "all" ? undefined : activeFilter;
        const data = await getReviewItems(PAGE_SIZE, 0, reviewReason);

        if (isCancelled) return;

        setItems(data.items.filter(isReviewableItem));
        setTotal(data.total);
        setNextOffset(data.offset + PAGE_SIZE);
        setHasMore(data.has_more);
      } catch (requestError) {
        if (isCancelled) return;

        if (requestError instanceof AdminApiError && requestError.status === 401) {
          onLogout();
          return;
        }

        if (requestError instanceof AdminApiError && requestError.status === 403) {
          onGoToChat();
          return;
        }

        setError("İnceleme kayıtları şu anda yüklenemiyor. Lütfen tekrar deneyin.");
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadReviewItems();

    return () => {
      isCancelled = true;
    };
  }, [activeFilter, onGoToChat, onLogout]);

  async function handleLoadMore() {
    if (isLoadingMore || !hasMore) return;

    setError("");
    setIsLoadingMore(true);

    try {
      const reviewReason = activeFilter === "all" ? undefined : activeFilter;
      const data = await getReviewItems(PAGE_SIZE, nextOffset, reviewReason);
      setItems((current) => [
        ...current,
        ...data.items.filter(isReviewableItem),
      ]);
      setTotal(data.total);
      setNextOffset(data.offset + PAGE_SIZE);
      setHasMore(data.has_more);
    } catch (requestError) {
      if (requestError instanceof AdminApiError && requestError.status === 401) {
        onLogout();
        return;
      }

      if (requestError instanceof AdminApiError && requestError.status === 403) {
        onGoToChat();
        return;
      }

      setError("Yeni kayıtlar yüklenemedi. Lütfen tekrar deneyin.");
    } finally {
      setIsLoadingMore(false);
    }
  }

  function handleFilterChange(filter: ReviewFilter) {
    if (filter === activeFilter || isLoading || isLoadingMore) return;

    setError("");
    setItems([]);
    setTotal(0);
    setNextOffset(PAGE_SIZE);
    setHasMore(false);
    setIsLoading(true);
    setActiveFilter(filter);
  }

  return (
    <AdminLayout
      user={user}
      activePage="review-items"
      pageTitle="İnceleme Kuyruğu"
      pageDescription="Kaynak bulunamayan, hatalı veya faydasız işaretlenen cevaplar"
      onGoToDashboard={onGoToDashboard}
      onGoToReviewItems={onGoToReviewItems}
      onGoToUsers={onGoToUsers}
      onGoToDocuments={onGoToDocuments}
      onGoToChat={onGoToChat}
      onLogout={onLogout}
    >
      <div className="admin-content review-page-content">
        {isLoading && (
          <div className="admin-loading" role="status">
            <span />
            İnceleme kayıtları yükleniyor...
          </div>
        )}

        {error && <div className="admin-error" role="alert">{error}</div>}

        {!isLoading && (
          <ReviewItemsList
            items={items}
            total={total}
            activeFilter={activeFilter}
            hasMore={hasMore}
            isLoadingMore={isLoadingMore}
            onFilterChange={handleFilterChange}
            onLoadMore={handleLoadMore}
          />
        )}
      </div>
    </AdminLayout>
  );
}

export default AdminReviewItemsPage;
