import type { ReactNode } from "react";
import type { CurrentUserResponse } from "../../../api/authApi";

interface AdminLayoutProps {
  user: CurrentUserResponse;
  children: ReactNode;
  activePage: "dashboard" | "review-items" | "users" | "documents" | "system-status";
  pageTitle: string;
  pageDescription?: string;
  onGoToDashboard: () => void;
  onGoToReviewItems: () => void;
  onGoToUsers: () => void;
  onGoToDocuments: () => void;
  onGoToSystemStatus: () => void;
  onGoToChat: () => void;
  onLogout: () => void;
}

function AdminLayout({
  user,
  children,
  activePage,
  pageTitle,
  pageDescription,
  onGoToDashboard,
  onGoToReviewItems,
  onGoToUsers,
  onGoToDocuments,
  onGoToSystemStatus,
  onGoToChat,
  onLogout,
}: AdminLayoutProps) {
  return (
    <div className="admin-shell">
      <aside className="admin-sidebar">
        <div className="admin-brand">
          <span className="admin-brand-mark">İZ</span>
          <div>
            <strong>İZELTAŞ</strong>
            <small>Yönetim Merkezi</small>
          </div>
        </div>

        <nav className="admin-nav" aria-label="Admin menüsü">
          <button
            className={`admin-nav-item ${activePage === "dashboard" ? "active" : ""}`}
            type="button"
            onClick={onGoToDashboard}
          >
            <span aria-hidden="true">▦</span>
            Dashboard
          </button>
          <button
            className={`admin-nav-item ${activePage === "review-items" ? "active" : ""}`}
            type="button"
            onClick={onGoToReviewItems}
          >
            <span aria-hidden="true">!</span>
            İnceleme Kuyruğu
          </button>
          <button
            className={`admin-nav-item ${activePage === "users" ? "active" : ""}`}
            type="button"
            onClick={onGoToUsers}
          >
            <span aria-hidden="true">◎</span>
            Kullanıcı Yönetimi
          </button>
          <button
            className={`admin-nav-item ${activePage === "documents" ? "active" : ""}`}
            type="button"
            onClick={onGoToDocuments}
          >
            <span aria-hidden="true">▤</span>
            Doküman Yönetimi
          </button>
          <button
            className={`admin-nav-item ${activePage === "system-status" ? "active" : ""}`}
            type="button"
            onClick={onGoToSystemStatus}
          >
            <span aria-hidden="true">◉</span>
            Sistem Durumu
          </button>
          <button className="admin-nav-item" type="button" onClick={onGoToChat}>
            <span aria-hidden="true">◇</span>
            Chat ekranı
          </button>
        </nav>

        <div className="admin-sidebar-footer">
          <div className="admin-profile">
            <span>{user.full_name.slice(0, 1).toLocaleUpperCase("tr-TR")}</span>
            <div>
              <strong>{user.full_name}</strong>
              <small>Yönetici</small>
            </div>
          </div>
          <button className="admin-logout" type="button" onClick={onLogout}>
            Çıkış yap
          </button>
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-topbar">
          <div>
            <span className="admin-page-eyebrow">Yönetim paneli</span>
            <h1>{pageTitle}</h1>
            {pageDescription && (
              <p className="admin-page-description">{pageDescription}</p>
            )}
          </div>
          <button type="button" className="admin-chat-link" onClick={onGoToChat}>
            Chat’e dön <span aria-hidden="true">→</span>
          </button>
        </header>
        {children}
      </main>
    </div>
  );
}

export default AdminLayout;
