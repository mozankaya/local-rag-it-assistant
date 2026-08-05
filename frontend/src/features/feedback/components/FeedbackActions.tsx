interface FeedbackActionsProps {
  status?: string;
  onFeedback: (feedback: "useful" | "not_useful") => void;
}

function FeedbackActions({ status, onFeedback }: FeedbackActionsProps) {
  return (
    <div className="feedback-area">
      <span>Bu yanıt yardımcı oldu mu?</span>

      <button
        className="feedback-button feedback-button-useful"
        type="button"
        aria-label="Yanıt faydalı"
        onClick={() => onFeedback("useful")}
      >
        Evet
      </button>

      <button
        className="feedback-button feedback-button-not-useful"
        type="button"
        aria-label="Yanıt faydalı değil"
        onClick={() => onFeedback("not_useful")}
      >
        Hayır
      </button>

      {status && <small role="status">{status}</small>}
    </div>
  );
}

export default FeedbackActions;
