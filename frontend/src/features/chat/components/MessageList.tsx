import type { ReactNode, RefObject } from "react";
import FeedbackActions from "../../feedback/components/FeedbackActions";
import type { Message } from "../types";
import SourceTooltip from "./SourceTooltip";

interface MessageListProps {
  children?: ReactNode;
  messages: Message[];
  isLoading: boolean;
  feedbackStatus: Record<number, string>;
  messagesEndRef: RefObject<HTMLDivElement | null>;
  onFeedback: (
    message: Message,
    feedback: "useful" | "not_useful",
  ) => void;
}

function MessageList({
  children,
  messages,
  isLoading,
  feedbackStatus,
  messagesEndRef,
  onFeedback,
}: MessageListProps) {
  return (
    <div
      className="messages"
      role="log"
      aria-label="Sohbet mesajları"
      aria-live="polite"
      aria-relevant="additions"
    >
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message-row ${
            message.role === "user"
              ? "message-row-user"
              : "message-row-assistant"
          }`}
        >
          {message.role === "assistant" && (
            <div className="message-avatar" aria-hidden="true">IT</div>
          )}

          <div className={`message-bubble ${message.role}`}>
            <p>{message.text}</p>

            {message.sources && message.sources.length > 0 && (
              <SourceTooltip sources={message.sources} />
            )}

            {message.role === "assistant"
              && typeof message.chatLogId === "number"
              && Number.isInteger(message.chatLogId)
              && message.chatLogId > 0 && (
              <FeedbackActions
                status={feedbackStatus[message.id]}
                onFeedback={(feedback) => onFeedback(message, feedback)}
              />
            )}
          </div>
        </div>
      ))}

      {children}

      {isLoading && (
        <div
          className="message-row message-row-assistant message-row-loading"
          role="status"
        >
          <div className="message-avatar" aria-hidden="true">IT</div>
          <div className="message-bubble assistant">
            <p>Yanıt hazırlanıyor...</p>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
}

export default MessageList;
