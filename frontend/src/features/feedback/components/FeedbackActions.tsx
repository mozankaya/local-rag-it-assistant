interface FeedbackActionsProps {
  status?: string;
  onFeedback: (feedback: "useful" | "not_useful") => void;
}

function FeedbackActions({ status, onFeedback }: FeedbackActionsProps) {
  return (
    <div className="feedback-area">
      <span>Bu yanıt yardımcı oldu mu?</span>

      <button
        type="button"
        onClick={() => onFeedback("useful")}
      >
        Evet
      </button>

      <button
        type="button"
        onClick={() => onFeedback("not_useful")}
      >
        Hayır
      </button>

      {status && <small>{status}</small>}
    </div>
  );
}

export default FeedbackActions;
