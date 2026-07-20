import { useEffect, useRef, useState } from "react";
import type { SyntheticEvent } from "react";
import {
  askQuestion,
  sendFeedback,
  type ChatResponse,
  type Source,
} from "../api/chatApi";

interface Message {
  id: number;
  role: "user" | "assistant";
  text: string;
  sources?: Source[];
  question?: string;
}

interface ChatBoxProps {
  quickQuestion: {
    id: number;
    question: string;
  } | null;
  resetSignal: number;
}

const starterQuestions = [
  "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
  "Şifremi unuttum, nasıl sıfırlayabilirim?",
  "Outlook mail göndermiyor, ne yapmalıyım?",
];

function createInitialMessages(): Message[] {
  return [
    {
      id: 1,
      role: "assistant",
      text: "Merhaba, ben İZELTAŞ IT Danışma Asistanı’yım. VPN, şifre, Outlook, yazıcı, donanım ve ağ bağlantısı gibi IT konularında yardımcı olabilirim.",
      sources: [],
    },
  ];
}

function formatSourceTitle(source: Source) {
  if (source.section_title) {
    return `${source.title || "Kaynak"} / ${source.section_title}`;
  }

  return source.title || source.document_id || "Kaynak";
}

function formatSourceMeta(source: Source) {
  const parts = [];

  if (source.category) parts.push(source.category);
  if (source.file_type) parts.push(source.file_type.toUpperCase());
  if (source.chunk_index) parts.push(`chunk ${source.chunk_index}`);

  return parts.join(" · ");
}

function ChatBox({ quickQuestion, resetSignal }: ChatBoxProps) {
  const [messages, setMessages] = useState<Message[]>(createInitialMessages);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState<Record<number, string>>(
    {},
  );

  const nextIdRef = useRef(2);
  const lastQuickQuestionIdRef = useRef<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  async function sendQuestion(questionText: string) {
    const cleanedQuestion = questionText.trim();

    if (!cleanedQuestion || isLoading) return;

    const userMessage: Message = {
      id: nextIdRef.current++,
      role: "user",
      text: cleanedQuestion,
    };

    setMessages((previous) => [...previous, userMessage]);
    setQuestion("");
    setIsLoading(true);

    try {
      const response: ChatResponse = await askQuestion(cleanedQuestion);

      const assistantMessage: Message = {
        id: nextIdRef.current++,
        role: "assistant",
        text: response.answer,
        sources: response.sources || [],
        question: response.question || cleanedQuestion,
      };

      setMessages((previous) => [...previous, assistantMessage]);
    } catch {
      const errorMessage: Message = {
        id: nextIdRef.current++,
        role: "assistant",
        text: "Chatbot servisine şu anda ulaşılamıyor. Lütfen daha sonra tekrar deneyin.",
        sources: [],
      };

      setMessages((previous) => [...previous, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSubmit(event?: SyntheticEvent<HTMLFormElement>) {
    event?.preventDefault();
    await sendQuestion(question);
  }

  async function handleStarterQuestion(value: string) {
    await sendQuestion(value);
  }

  async function handleFeedback(
    message: Message,
    feedback: "useful" | "not_useful",
  ) {
    if (!message.question) return;

    try {
      await sendFeedback({
        question: message.question,
        answer: message.text,
        feedback,
        sources: message.sources || [],
      });

      setFeedbackStatus((previous) => ({
        ...previous,
        [message.id]:
          feedback === "useful"
            ? "Faydalı olarak kaydedildi."
            : "Faydasız olarak kaydedildi.",
      }));
    } catch {
      setFeedbackStatus((previous) => ({
        ...previous,
        [message.id]: "Geri bildirim gönderilemedi.",
      }));
    }
  }

  useEffect(() => {
    setMessages(createInitialMessages());
    setQuestion("");
    setFeedbackStatus({});
    nextIdRef.current = 2;
  }, [resetSignal]);

  useEffect(() => {
    if (!quickQuestion) return;

    if (lastQuickQuestionIdRef.current === quickQuestion.id) return;

    lastQuickQuestionIdRef.current = quickQuestion.id;
    void sendQuestion(quickQuestion.question);
  }, [quickQuestion]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, isLoading]);

  return (
    <div className="chat-box">
      <div className="starter-row">
        {starterQuestions.map((starterQuestion) => (
          <button
            key={starterQuestion}
            type="button"
            onClick={() => handleStarterQuestion(starterQuestion)}
          >
            {starterQuestion}
          </button>
        ))}
      </div>

      <div className="messages">
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
              <div className="message-avatar">IT</div>
            )}

            <div className={`message-bubble ${message.role}`}>
              <p>{message.text}</p>

              {message.sources && message.sources.length > 0 && (
                <div className="source-tooltip-wrapper">
                  <button
                    className="source-tooltip-trigger"
                    type="button"
                    aria-label="Kaynakları göster"
                  >
                    ⓘ Kaynak
                  </button>

                  <div className="source-tooltip-panel">
                    <h4>Kaynaklar</h4>

                    <div className="source-tooltip-list">
                      {message.sources.map((source, index) => (
                        <div
                          className="source-tooltip-item"
                          key={`${source.document_id}-${index}`}
                        >
                          <span className="source-icon">▣</span>

                          <div>
                            <strong>{formatSourceTitle(source)}</strong>
                            <small>{formatSourceMeta(source)}</small>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {message.role === "assistant" && message.question && (
                <div className="feedback-area">
                  <span>Bu yanıt yardımcı oldu mu?</span>

                  <button
                    type="button"
                    onClick={() => handleFeedback(message, "useful")}
                  >
                    Evet
                  </button>

                  <button
                    type="button"
                    onClick={() => handleFeedback(message, "not_useful")}
                  >
                    Hayır
                  </button>

                  {feedbackStatus[message.id] && (
                    <small>{feedbackStatus[message.id]}</small>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message-row message-row-assistant">
            <div className="message-avatar">IT</div>
            <div className="message-bubble assistant">
              <p>Yanıt hazırlanıyor...</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSubmit}>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Mesajınızı buraya yazın..."
          rows={2}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void sendQuestion(question);
            }
          }}
        />

        <button type="submit" disabled={isLoading || !question.trim()}>
          Gönder
        </button>
      </form>
    </div>
  );
}

export default ChatBox;
