import { useEffect, useRef, useState } from "react";
import type { SyntheticEvent } from "react";
import { askQuestion, sendFeedback } from "../api/chatApi";
import type { FeedbackValue, Source } from "../api/chatApi";

type FeedbackStatus = "idle" | "sending" | "sent" | "error";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  question?: string;
  sources?: Source[];
  feedback?: FeedbackValue;
  feedbackStatus?: FeedbackStatus;
};

const quickQuestions = [
  {
    label: "VPN",
    question: "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
  },
  {
    label: "Şifre",
    question: "Şifremi unuttum, nasıl sıfırlayabilirim?",
  },
  {
    label: "Yazıcı",
    question: "Yazıcıdan çıktı alamıyorum, ne yapmalıyım?",
  },
  {
    label: "Outlook",
    question: "Outlook e-posta göndermiyor, ne yapmalıyım?",
  },
  {
    label: "Donanım",
    question: "Bilgisayarım çok yavaş, ne yapmalıyım?",
  },
];

function createMessageId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formatFeedbackText(feedback?: FeedbackValue) {
  if (feedback === "useful") return "Faydalı";
  if (feedback === "not_useful") return "Faydasız";
  return "";
}

export default function ChatBox() {
  const messageListRef = useRef<HTMLDivElement | null>(null);
  const [inputValue, setInputValue] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-message",
      role: "assistant",
      content:
        "Merhaba. IT süreçleri, VPN, şifre, Outlook, yazıcı, donanım ve ağ bağlantısı gibi konularda yardımcı olabilirim.",
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const messageList = messageListRef.current;

    if (!messageList) {
      return;
    }

    messageList.scrollTo({
      top: messageList.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isLoading]);

  async function submitQuestion(questionText?: string) {
    const trimmedQuestion = (questionText ?? inputValue).trim();

    if (!trimmedQuestion || isLoading) {
      return;
    }

    setInputValue("");
    setErrorMessage(null);

    const userMessage: Message = {
      id: createMessageId("user"),
      role: "user",
      content: trimmedQuestion,
    };

    setMessages((previous) => [...previous, userMessage]);
    setIsLoading(true);

    try {
      const result = await askQuestion(trimmedQuestion);

      const assistantMessage: Message = {
        id: createMessageId("assistant"),
        role: "assistant",
        content: result.answer,
        question: trimmedQuestion,
        sources: result.sources || [],
        feedbackStatus: "idle",
      };

      setMessages((previous) => [...previous, assistantMessage]);
    } catch {
      setErrorMessage(
        "Cevap alınırken bir hata oluştu. n8n workflow, Ollama servisi veya webhook URL ayarlarını kontrol edin.",
      );

      const assistantErrorMessage: Message = {
        id: createMessageId("assistant-error"),
        role: "assistant",
        content:
          "Şu anda cevap alınamadı. Lütfen sistem servislerinin çalıştığını kontrol edin.",
      };

      setMessages((previous) => [...previous, assistantErrorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    void submitQuestion();
  }

  async function handleFeedback(messageId: string, feedback: FeedbackValue) {
    const message = messages.find((item) => item.id === messageId);

    if (!message || message.role !== "assistant" || !message.question) {
      return;
    }

    setMessages((previous) =>
      previous.map((item) =>
        item.id === messageId
          ? {
              ...item,
              feedbackStatus: "sending",
            }
          : item,
      ),
    );

    try {
      await sendFeedback({
        question: message.question,
        answer: message.content,
        feedback,
        sources: message.sources,
      });

      setMessages((previous) =>
        previous.map((item) =>
          item.id === messageId
            ? {
                ...item,
                feedback,
                feedbackStatus: "sent",
              }
            : item,
        ),
      );
    } catch {
      setMessages((previous) =>
        previous.map((item) =>
          item.id === messageId
            ? {
                ...item,
                feedbackStatus: "error",
              }
            : item,
        ),
      );
    }
  }

  return (
    <section className="chat-layout">
      <section className="chat-panel">
        <header className="chat-header">
          <div className="chat-header-content">
            <p className="eyebrow">Local LLM & RAG</p>
            <h1>İZELTAŞ IT DANIŞMA ASİSTANI</h1>

            <p className="chat-description">
              Bu arayüz, lokal çalışan RAG tabanlı IT destek asistanının demo
              ekranıdır. Cevaplar mock IT dokümanlarından alınan kaynaklara göre
              oluşturulur.
            </p>

            <div className="quick-question-section">
              <h2>Hazır Sorular</h2>
              <div className="quick-question-list">
                {quickQuestions.map((item) => (
                  <button
                    key={item.label}
                    type="button"
                    className="quick-question-button"
                    disabled={isLoading}
                    onClick={() => void submitQuestion(item.question)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="connection-badge">
            <span className="connection-dot"></span>
            Lokal prototip
          </div>
        </header>

        <div className="message-list" ref={messageListRef}>
          {messages.map((message) => (
            <article
              key={message.id}
              className={`message-row ${
                message.role === "user" ? "user-row" : "assistant-row"
              }`}
            >
              <div className={`message-bubble ${message.role}`}>
                <div className="message-label">
                  {message.role === "user" ? "Siz" : "Asistan"}
                </div>

                <div className="message-content">
                  {message.content
                    .split("\n")
                    .map((line, lineIndex) =>
                      line.trim() ? <p key={lineIndex}>{line}</p> : null,
                    )}
                </div>

                {message.role === "assistant" &&
                  message.sources &&
                  message.sources.length > 0 && (
                    <div className="source-tooltip-wrapper">
                      <button className="source-chip" type="button">
                        ⓘ Kaynaklar ({message.sources.length})
                      </button>

                      <div className="source-tooltip">
                        {message.sources.map((source, sourceIndex) => (
                          <div
                            key={`${source.document_id}-${source.chunk_index}-${sourceIndex}`}
                            className="source-tooltip-item"
                          >
                            <strong>{source.title}</strong>
                            <span>
                              {source.category} / chunk {source.chunk_index}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                {message.role === "assistant" && message.question && (
                  <div className="feedback-area">
                    {message.feedbackStatus === "sent" ? (
                      <span className="feedback-saved">
                        Geri bildiriminiz kaydedildi:{" "}
                        {formatFeedbackText(message.feedback)}
                      </span>
                    ) : (
                      <>
                        <button
                          type="button"
                          className="feedback-button"
                          disabled={message.feedbackStatus === "sending"}
                          onClick={() =>
                            void handleFeedback(message.id, "useful")
                          }
                        >
                          👍 Faydalı
                        </button>

                        <button
                          type="button"
                          className="feedback-button"
                          disabled={message.feedbackStatus === "sending"}
                          onClick={() =>
                            void handleFeedback(message.id, "not_useful")
                          }
                        >
                          👎 Faydasız
                        </button>
                      </>
                    )}

                    {message.feedbackStatus === "sending" && (
                      <span className="feedback-info">
                        Geri bildirim kaydediliyor...
                      </span>
                    )}

                    {message.feedbackStatus === "error" && (
                      <span className="feedback-error">
                        Geri bildirim kaydedilemedi.
                      </span>
                    )}
                  </div>
                )}
              </div>
            </article>
          ))}

          {isLoading && (
            <article className="message-row assistant-row">
              <div className="message-bubble assistant loading-bubble">
                <div className="message-label">Asistan</div>
                <div
                  className="typing-indicator"
                  aria-label="Cevap hazırlanıyor"
                >
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </article>
          )}
        </div>

        {errorMessage && <div className="error-banner">{errorMessage}</div>}

        <form className="chat-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={inputValue}
            disabled={isLoading}
            placeholder="Örn: VPN bağlantısı kuramıyorum..."
            onChange={(event) => setInputValue(event.target.value)}
          />
          <button type="submit" disabled={isLoading || !inputValue.trim()}>
            Gönder
          </button>
        </form>
      </section>
    </section>
  );
}
