import { useEffect, useState } from "react";
import {
  AdminApiError,
  getCategories,
  getDashboardSummary,
  getFeedbackSummary,
  getReviewItems,
  getResponseTypes,
  type CategoryCount,
  type DashboardSummary,
  type FeedbackSummary,
  type ReviewItem,
  type ResponseTypeCount,
} from "../../api/adminApi";
import type { CurrentUserResponse } from "../../api/authApi";
import AdminLayout from "./AdminLayout";
import DistributionCard from "./DistributionCard";
import ReviewItemsList from "./ReviewItemsList";
import SummaryCards from "./SummaryCards";
import "./admin.css";

interface AdminDashboardPageProps {
  user: CurrentUserResponse;
  onGoToChat: () => void;
  onLogout: () => void;
}

const responseTypeLabels: Record<string, string> = {
  success: "Başarılı yanıt",
  no_relevant_source: "İlgili kaynak yok",
  out_of_scope: "Kapsam dışı",
  llm_error: "LLM hatası",
  unknown: "Bilinmiyor",
};

function humanize(value: string) {
  return value.replaceAll("_", " ").replace(/^./, (letter) => letter.toLocaleUpperCase("tr-TR"));
}

function isReviewableItem(item: ReviewItem) {
  return item.review_reason !== "useful"
    && item.feedback !== "useful"
    && item.response_type !== "rag_answer";
}

function AdminDashboardPage({ user, onGoToChat, onLogout }: AdminDashboardPageProps) {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [feedback, setFeedback] = useState<FeedbackSummary | null>(null);
  const [responseTypes, setResponseTypes] = useState<ResponseTypeCount[]>([]);
  const [categories, setCategories] = useState<CategoryCount[]>([]);
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([]);
  const [reviewTotal, setReviewTotal] = useState(0);
  const [nextReviewOffset, setNextReviewOffset] = useState(20);
  const [hasMore, setHasMore] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [summaryData, responseData, categoryData, feedbackData, reviewData] =
          await Promise.all([
            getDashboardSummary(),
            getResponseTypes(),
            getCategories(),
            getFeedbackSummary(),
            getReviewItems(20, 0),
          ]);

        setSummary(summaryData);
        setResponseTypes(responseData);
        setCategories(categoryData);
        setFeedback(feedbackData);
        setReviewItems(reviewData.items.filter(isReviewableItem));
        setReviewTotal(reviewData.total);
        setNextReviewOffset(reviewData.offset + reviewData.limit);
        setHasMore(reviewData.has_more);
      } catch (requestError) {
        if (requestError instanceof AdminApiError && requestError.status === 401) {
          onLogout();
          return;
        }

        if (requestError instanceof AdminApiError && requestError.status === 403) {
          onGoToChat();
          return;
        }

        setError("Dashboard verileri şu anda yüklenemiyor. Lütfen tekrar deneyin.");
      } finally {
        setIsLoading(false);
      }
    }

    void loadDashboard();
  }, [onGoToChat, onLogout]);

  async function handleLoadMore() {
    if (isLoadingMore || !hasMore) return;
    setIsLoadingMore(true);

    try {
      const reviewData = await getReviewItems(20, nextReviewOffset);
      setReviewItems((current) => [
        ...current,
        ...reviewData.items.filter(isReviewableItem),
      ]);
      setReviewTotal(reviewData.total);
      setNextReviewOffset(reviewData.offset + reviewData.limit);
      setHasMore(reviewData.has_more);
    } catch {
      setError("Yeni inceleme kayıtları yüklenemedi. Lütfen tekrar deneyin.");
    } finally {
      setIsLoadingMore(false);
    }
  }

  return (
    <AdminLayout user={user} onGoToChat={onGoToChat} onLogout={onLogout}>
      <div className="admin-content">
        {isLoading && (
          <div className="admin-loading" role="status">
            <span />
            Dashboard verileri yükleniyor...
          </div>
        )}

        {error && <div className="admin-error" role="alert">{error}</div>}

        {!isLoading && summary && feedback && (
          <>
            <SummaryCards summary={summary} feedback={feedback} />

            <section className="admin-distribution-grid">
              <DistributionCard
                title="Response type dağılımı"
                subtitle="Üretilen yanıtların sonuç türleri"
                items={responseTypes.map((item) => ({
                  label: responseTypeLabels[item.response_type] ?? humanize(item.response_type),
                  count: item.count,
                }))}
                emptyText="Yanıt türü verisi bulunmuyor."
              />
              <DistributionCard
                title="Kategori dağılımı"
                subtitle="Soruların konu başlıklarına göre dağılımı"
                items={categories.map((item) => ({
                  label: humanize(item.category),
                  count: item.count,
                }))}
                emptyText="Kategori verisi bulunmuyor."
              />
            </section>

            <ReviewItemsList
              items={reviewItems}
              total={reviewTotal}
              hasMore={hasMore}
              isLoadingMore={isLoadingMore}
              onLoadMore={handleLoadMore}
            />
          </>
        )}
      </div>
    </AdminLayout>
  );
}

export default AdminDashboardPage;
