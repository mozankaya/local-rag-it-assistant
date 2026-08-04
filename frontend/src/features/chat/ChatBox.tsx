import { useCallback, useEffect, useRef, useState } from "react";
import type { SyntheticEvent } from "react";
import {
  askQuestion,
  ChatApiError,
  sendFeedback,
  type ChatResponse,
} from "../../api/chatApi";
import MessageList from "./components/MessageList";
import type { Message } from "./types";

interface ChatBoxProps {
  quickQuestion: {
    id: number;
    question: string;
  } | null;
  onUnauthorized: () => void;
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

function ChatBox({ quickQuestion, onUnauthorized }: ChatBoxProps) {
  const [messages, setMessages] = useState<Message[]>(createInitialMessages);
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [feedbackStatus, setFeedbackStatus] = useState<Record<number, string>>(
    {},
  );

  const nextIdRef = useRef(2);
  const lastQuickQuestionIdRef = useRef<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const sendQuestion = useCallback(async (questionText: string) => {
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
        chatLogId: response.chat_log_id,
      };

      setMessages((previous) => [...previous, assistantMessage]);
    } catch (error) {
      if (error instanceof ChatApiError && error.status === 401) {
        onUnauthorized();
        return;
      }

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
  }, [isLoading, onUnauthorized]);

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
    if (
      typeof message.chatLogId !== "number"
      || !Number.isInteger(message.chatLogId)
      || message.chatLogId <= 0
    ) return;

    try {
      await sendFeedback({
        chat_log_id: message.chatLogId,
        feedback,
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
    if (!quickQuestion) return;

    if (lastQuickQuestionIdRef.current === quickQuestion.id) return;

    lastQuickQuestionIdRef.current = quickQuestion.id;
    void sendQuestion(quickQuestion.question);
  }, [quickQuestion, sendQuestion]);

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

      <MessageList
        messages={messages}
        isLoading={isLoading}
        feedbackStatus={feedbackStatus}
        messagesEndRef={messagesEndRef}
        onFeedback={handleFeedback}
      />

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
