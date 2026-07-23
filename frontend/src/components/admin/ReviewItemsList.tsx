import type { ReviewItem } from "../../api/adminApi";

interface ReviewItemsListProps {
  items: ReviewItem[];
  total: number;
  hasMore: boolean;
  isLoadingMore: boolean;
  onLoadMore: () => void;
}

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
  hasMore,
  isLoadingMore,
  onLoadMore,
}: ReviewItemsListProps) {
  return (
    <article className="admin-panel recent-panel">
      <div className="admin-panel-header">
        <div>
          <h2>İncelenmesi Gereken Kayıtlar</h2>
          <p>Olumsuz feedback ve teknik sorun içeren yanıtlar</p>
        </div>
        <span className="admin-total-pill">{total} kayıt</span>
      </div>

      {items.length === 0 ? (
        <p className="admin-empty">İncelenmesi gereken kayıt bulunmuyor.</p>
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
        >
          {isLoadingMore ? "Yükleniyor..." : "Daha fazla göster"}
        </button>
      )}
    </article>
  );
}

export default ReviewItemsList;
