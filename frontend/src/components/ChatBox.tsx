import { useState } from "react";
import { askQuestion } from "../api/chatApi";

type Message = {
  role: "user" | "assistant";
  content: string;
};

export default function ChatBox() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuestion = question.trim();

    if (!trimmedQuestion) {
      return;
    }

    setError("");
    setIsLoading(true);
    setQuestion("");

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: trimmedQuestion,
      },
    ]);

    try {
      const result = await askQuestion(trimmedQuestion);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: result.answer,
        },
      ]);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Beklenmeyen bir hata oluştu.";

      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="chat-card">
      <div className="chat-header">
        <div>
          <h1>İZELTAŞ IT Danışma Asistanı</h1>
          <p>Lokal LLM ve RAG tabanlı IT destek prototipi</p>
        </div>
        <span className="status-badge">v1 Prototype</span>
      </div>

      <div className="messages">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>Bir IT destek sorusu yazarak başlayabilirsiniz.</p>
            <div className="examples">
              <button onClick={() => setQuestion("VPN bağlantısı kuramıyorum, ne yapmalıyım?")}>
                VPN bağlantısı kuramıyorum
              </button>
              <button onClick={() => setQuestion("Şifremi unuttum, nasıl sıfırlayabilirim?")}>
                Şifremi unuttum
              </button>
              <button onClick={() => setQuestion("Yazıcıdan çıktı alamıyorum.")}>
                Yazıcıdan çıktı alamıyorum
              </button>
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`message ${message.role}`}
            >
              <div className="message-label">
                {message.role === "user" ? "Kullanıcı" : "Asistan"}
              </div>
              <div className="message-content">{message.content}</div>
            </div>
          ))
        )}
      </div>

      {error && <div className="error-box">Hata: {error}</div>}

      <form onSubmit={handleSubmit} className="input-area">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Örn: VPN bağlantısı kuramıyorum..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !question.trim()}>
          {isLoading ? "Yanıtlanıyor..." : "Gönder"}
        </button>
      </form>
    </div>
  );
}