import { useCallback, useEffect, useRef, useState } from "react";
import {
  clearAccessToken,
  getAccessToken,
  getCurrentUser,
  type CurrentUserResponse,
} from "../api/authApi";
import AdminDashboardPage from "../features/admin/dashboard/AdminDashboardPage";
import AdminDocumentsPage from "../features/admin/documents/AdminDocumentsPage";
import AdminReviewItemsPage from "../features/admin/review-queue/AdminReviewItemsPage";
import AdminSystemStatusPage from "../features/admin/system-status/AdminSystemStatusPage";
import AdminUsersPage from "../features/admin/users/AdminUsersPage";
import LoginPage from "../features/auth/LoginPage";
import ChatPage from "../features/chat/ChatPage";
import "../App.css";

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
      || pathname === "/admin/review-items"
      || pathname === "/admin/users"
      || pathname === "/admin/documents"
      || pathname === "/admin/system-status";

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

  const handleGoToUsers = useCallback(() => {
    navigate("/admin/users");
  }, [navigate]);

  const handleGoToDocuments = useCallback(() => {
    navigate("/admin/documents");
  }, [navigate]);

  const handleGoToSystemStatus = useCallback(() => {
    navigate("/admin/system-status");
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
        onGoToUsers={handleGoToUsers}
        onGoToDocuments={handleGoToDocuments}
        onGoToSystemStatus={handleGoToSystemStatus}
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
        onGoToUsers={handleGoToUsers}
        onGoToDocuments={handleGoToDocuments}
        onGoToSystemStatus={handleGoToSystemStatus}
        onGoToChat={handleGoToChat}
        onLogout={handleLogout}
      />
    );
  }

  if (currentUser.role === "admin" && pathname === "/admin/users") {
    return (
      <AdminUsersPage
        user={currentUser}
        onGoToDashboard={handleGoToDashboard}
        onGoToReviewItems={handleGoToReviewItems}
        onGoToUsers={handleGoToUsers}
        onGoToDocuments={handleGoToDocuments}
        onGoToSystemStatus={handleGoToSystemStatus}
        onGoToChat={handleGoToChat}
        onLogout={handleLogout}
      />
    );
  }

  if (currentUser.role === "admin" && pathname === "/admin/documents") {
    return (
      <AdminDocumentsPage
        user={currentUser}
        onGoToDashboard={handleGoToDashboard}
        onGoToReviewItems={handleGoToReviewItems}
        onGoToUsers={handleGoToUsers}
        onGoToDocuments={handleGoToDocuments}
        onGoToSystemStatus={handleGoToSystemStatus}
        onGoToChat={handleGoToChat}
        onLogout={handleLogout}
      />
    );
  }

  if (currentUser.role === "admin" && pathname === "/admin/system-status") {
    return (
      <AdminSystemStatusPage
        user={currentUser}
        onGoToDashboard={handleGoToDashboard}
        onGoToReviewItems={handleGoToReviewItems}
        onGoToUsers={handleGoToUsers}
        onGoToDocuments={handleGoToDocuments}
        onGoToSystemStatus={handleGoToSystemStatus}
        onGoToChat={handleGoToChat}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <ChatPage
      user={currentUser}
      quickQuestion={quickQuestion}
      resetSignal={resetSignal}
      onQuickTopic={handleQuickTopic}
      onNewChat={handleNewChat}
      onGoToAdmin={handleGoToDashboard}
      onLogout={handleLogout}
    />
  );
}

export default App;
