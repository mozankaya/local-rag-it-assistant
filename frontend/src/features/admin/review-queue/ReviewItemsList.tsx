import type { ReviewItem } from "../../../api/adminApi";

export type ReviewFilter =
  | "all"
  | "no_relevant_source"
  | "not_useful"
  | "llm_error";

interface ReviewItemsListProps {
  items: ReviewItem[];
  total: number;
  activeFilter: ReviewFilter;
  hasMore: boolean;
  isLoadingMore: boolean;
  onFilterChange: (filter: ReviewFilter) => void;
  onLoadMore: () => void;
}

const filterOptions: Array<{ value: ReviewFilter; label: string }> = [
  { value: "all", label: "Tümü" },
  { value: "no_relevant_source", label: "Kaynak bulunamadı" },
  { value: "not_useful", label: "Faydasız feedback" },
  { value: "llm_error", label: "LLM hatası" },
];

const reviewReasonLabels: Record<string, string> = {
  not_useful: "Faydasız feedback",
  no_relevant_source: "Kaynak bulunamadı",
  llm_error: "LLM hatası",
};

const valueLabels: Record<string, string> = {
  not_useful: "Faydasız",
  no_relevant_source: "Kaynak bulunamadı",
  llm_error: "LLM hatası",
  out_of_scope: "Kapsam dışı",
  unknown: "Bilinmiyor",
};

function humanize(value: string) {
  return value
    .replaceAll("_", " ")
    .replace(/^./, (letter) => letter.toLocaleUpperCase("tr-TR"));
}

function formatDate(value: string) {
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

function ReviewItemsList({
  items,
  total,
  activeFilter,
  hasMore,
  isLoadingMore,
  onFilterChange,
  onLoadMore,
}: ReviewItemsListProps) {
  return (
    <article className="admin-panel recent-panel">
      <div className="admin-panel-header">
        <div>
          <h2>İnceleme kayıtları</h2>
          <p>Yüklenen kayıtları inceleme nedenine göre filtreleyin</p>
        </div>
        <span className="admin-total-pill">{total} kayıt</span>
      </div>

      <div className="review-filter-bar" aria-label="İnceleme kayıtlarını filtrele">
        {filterOptions.map((option) => (
          <button
            className={`review-filter-button ${activeFilter === option.value ? "active" : ""}`}
            type="button"
            key={option.value}
            aria-pressed={activeFilter === option.value}
            disabled={isLoadingMore}
            onClick={() => onFilterChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>

      {items.length === 0 ? (
        isLoadingMore ? (
          <div className="admin-filter-loading" role="status">
            <span />
            Uygun kayıtlar aranıyor...
          </div>
        ) : (
          <p className="admin-empty">Bu filtreye uygun kayıt bulunmuyor.</p>
        )
      ) : (
        <div className="recent-question-list">
          {items.map((item) => (
            <div
              className="recent-question"
              key={`${item.item_type}-${item.item_id}`}
            >
              <span className="question-index">
                {String(item.item_id).padStart(2, "0")}
              </span>

              <div className="question-copy">
                <strong>{item.question}</strong>
                {item.answer_preview && <p>{item.answer_preview}</p>}

                <div className="question-tags">
                  {item.category && <span>{item.category}</span>}
                  {item.section_title && <span>{item.section_title}</span>}
                  {item.item_type === "feedback" && item.feedback && (
                    <span className="record-detail-tag">
                      Feedback: {valueLabels[item.feedback] ?? humanize(item.feedback)}
                    </span>
                  )}
                  {item.item_type === "chat_log" && item.response_type && (
                    <span className="record-detail-tag">
                      Yanıt: {valueLabels[item.response_type] ?? humanize(item.response_type)}
                    </span>
                  )}
                </div>
              </div>

              <div className="question-status">
                <span className={`review-reason-badge reason-${item.review_reason}`}>
                  {reviewReasonLabels[item.review_reason] ?? humanize(item.review_reason)}
                </span>
                {item.created_at && (
                  <time dateTime={item.created_at}>{formatDate(item.created_at)}</time>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {hasMore && (
        <button
          className="load-more-button"
          type="button"
          onClick={onLoadMore}
          disabled={isLoadingMore}
          aria-busy={isLoadingMore}
        >
          {isLoadingMore ? "Yükleniyor..." : "Daha fazla göster"}
        </button>
      )}
    </article>
  );
}

export default ReviewItemsList;
