import { useCallback, useEffect, useRef, useState } from "react";
import {
  clearAccessToken,
  getAccessToken,
  getCurrentUser,
  type CurrentUserResponse,
} from "./api/authApi";
import ChatBox from "./components/ChatBox";
import LoginPage from "./components/LoginPage";
import AdminDashboardPage from "./components/admin/AdminDashboardPage";
import AdminReviewItemsPage from "./components/admin/AdminReviewItemsPage";
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
  const [currentUser, setCurrentUser] = useState<CurrentUserResponse | null>(
    null,
  );
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [quickQuestion, setQuickQuestion] = useState<{
    id: number;
    question: string;
  } | null>(null);
  const [resetSignal, setResetSignal] = useState(0);
  const [pathname, setPathname] = useState(window.location.pathname);
  const quickQuestionIdRef = useRef(0);

  const navigate = useCallback((path: string, replace = false) => {
    if (replace) {
      window.history.replaceState({}, "", path);
    } else {
      window.history.pushState({}, "", path);
    }

    setPathname(path);
  }, []);

  useEffect(() => {
    async function checkExistingSession() {
      const token = getAccessToken();

      if (!token) {
        setIsCheckingAuth(false);
        return;
      }

      try {
        const user = await getCurrentUser();
        setCurrentUser(user);
      } catch {
        clearAccessToken();
        setCurrentUser(null);
      } finally {
        setIsCheckingAuth(false);
      }
    }

    void checkExistingSession();
  }, []);

  useEffect(() => {
    function handlePopState() {
      setPathname(window.location.pathname);
    }

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    if (!currentUser || !pathname.startsWith("/admin")) return;

    if (currentUser.role !== "admin") {
      window.location.replace("/");
      return;
    }

    const isKnownAdminRoute = pathname === "/admin/dashboard"
      || pathname === "/admin/review-items";

    if (!isKnownAdminRoute) {
      window.location.replace("/admin/dashboard");
    }
  }, [currentUser, pathname]);

  function handleQuickTopic(question: string) {
    quickQuestionIdRef.current += 1;
    setQuickQuestion({
      id: quickQuestionIdRef.current,
      question,
    });
  }

  function handleNewChat() {
    setResetSignal((previous) => previous + 1);
    setQuickQuestion(null);
  }

  const handleLogout = useCallback(() => {
    clearAccessToken();
    setCurrentUser(null);
    setResetSignal((previous) => previous + 1);
    setQuickQuestion(null);
    navigate("/", true);
  }, [navigate]);

  const handleGoToChat = useCallback(() => {
    navigate("/");
  }, [navigate]);

  const handleGoToDashboard = useCallback(() => {
    navigate("/admin/dashboard");
  }, [navigate]);

  const handleGoToReviewItems = useCallback(() => {
    navigate("/admin/review-items");
  }, [navigate]);

  if (isCheckingAuth) {
    return (
      <div className="auth-loading">
        <div className="login-icon">IT</div>
        <p>Oturum kontrol ediliyor...</p>
      </div>
    );
  }

  if (!currentUser) {
    return <LoginPage onLoginSuccess={setCurrentUser} />;
  }

  if (currentUser.role === "admin" && pathname === "/admin/dashboard") {
    return (
      <AdminDashboardPage
        user={currentUser}
        onGoToDashboard={handleGoToDashboard}
        onGoToReviewItems={handleGoToReviewItems}
        onGoToChat={handleGoToChat}
        onLogout={handleLogout}
      />
    );
  }

  if (currentUser.role === "admin" && pathname === "/admin/review-items") {
    return (
      <AdminReviewItemsPage
        user={currentUser}
        onGoToDashboard={handleGoToDashboard}
        onGoToReviewItems={handleGoToReviewItems}
        onGoToChat={handleGoToChat}
        onLogout={handleLogout}
      />
    );
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

          <div className="user-chip">
            {currentUser.full_name} · {currentUser.role}
          </div>

          {currentUser.role === "admin" && (
            <button
              className="admin-button"
              type="button"
              onClick={() => navigate("/admin/dashboard")}
            >
              Admin Panel
            </button>
          )}

          <button
            className="logout-button"
            type="button"
            onClick={handleLogout}
          >
            Çıkış
          </button>
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
            <strong>itdestek@izeltas.com</strong>
            <span>0232 XXX XX XX</span>
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

          <ChatBox key={resetSignal} quickQuestion={quickQuestion} />
        </section>
      </main>
    </div>
  );
}

export default App;
