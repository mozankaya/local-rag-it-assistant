import { useState } from "react";
import ChatBox from "./components/ChatBox";
import "./App.css";

const quickTopics = [
  {
    label: "VPN",
    question: "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
  },
  {
    label: "Şifre",
    question: "Şifremi unuttum, nasıl sıfırlayabilirim?",
  },
  {
    label: "Outlook",
    question: "Outlook mail göndermiyor, ne yapmalıyım?",
  },
  {
    label: "Yazıcı",
    question: "Yazıcıdan çıktı alamıyorum, ne yapmalıyım?",
  },
  {
    label: "Donanım",
    question: "Donanım desteği talebi nasıl oluşturabilirim?",
  },
  {
    label: "Ağ",
    question: "İnternet bağlantım yok, ne yapmalıyım?",
  },
];

function App() {
  const [quickQuestion, setQuickQuestion] = useState<{
    id: number;
    question: string;
  } | null>(null);

  const [resetSignal, setResetSignal] = useState(0);

  function handleQuickTopic(question: string) {
    setQuickQuestion({
      id: Date.now(),
      question,
    });
  }

  function handleNewChat() {
    setResetSignal((previous) => previous + 1);
    setQuickQuestion(null);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-area">
          <div className="brand-logo">IZELTAS</div>
          <div className="brand-divider" />
          <div>
            <h1>İZELTAŞ IT Danışma Asistanı</h1>
            <p>Lokal LLM & RAG destekli IT yardım sistemi</p>
          </div>
        </div>

        <div className="topbar-right">
          <span className="status-dot" />
          <span>Çevrimiçi</span>
          <div className="user-chip">Demo Kullanıcı</div>
        </div>
      </header>

      <main className="dashboard-layout">
        <aside className="sidebar">
          <div className="assistant-card">
            <div className="assistant-icon">IT</div>

            <h2>İZELTAŞ IT Danışma Asistanı</h2>
            <p>
              IT ile ilgili sorularınızda size hızlı ve doğru destek olmak için
              buradayım. Aşağıdaki konulardan birini seçebilir veya sorunuzu
              yazabilirsiniz.
            </p>
          </div>

          <div className="quick-topics">
            <h3>Hızlı Konular</h3>

            <div className="topic-grid">
              {quickTopics.map((topic) => (
                <button
                  key={topic.label}
                  type="button"
                  onClick={() => handleQuickTopic(topic.question)}
                >
                  {topic.label}
                </button>
              ))}
            </div>
          </div>

          <div className="announcement-card">
            <h3>Duyurular</h3>
            <p>
              Sistem bakım ve destek süreçleri hakkında güncel bilgilendirmeler
              burada gösterilebilir.
            </p>
          </div>

          <div className="support-info">
            <p>Yardım ve destek için:</p>
            <strong>itdestek@izeltas.com.tr</strong>
            <span>0232 472 13 75</span>
          </div>
        </aside>

        <section className="chat-panel">
          <div className="chat-panel-header">
            <div>
              <h2>Sohbet</h2>
              <span>IT destek dokümanlarına göre cevap üretir</span>
            </div>

            <button
              className="new-chat-button"
              type="button"
              onClick={handleNewChat}
            >
              Yeni Sohbet
            </button>
          </div>

          <ChatBox quickQuestion={quickQuestion} resetSignal={resetSignal} />
        </section>
      </main>
    </div>
  );
}

export default App;
