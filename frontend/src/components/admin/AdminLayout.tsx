import type { ReactNode } from "react";
import type { CurrentUserResponse } from "../../api/authApi";

interface AdminLayoutProps {
  user: CurrentUserResponse;
  children: ReactNode;
  onGoToChat: () => void;
  onLogout: () => void;
}

function AdminLayout({ user, children, onGoToChat, onLogout }: AdminLayoutProps) {
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
          <button className="admin-nav-item active" type="button">
            <span aria-hidden="true">▦</span>
            Dashboard
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
            <p>Yönetim paneli</p>
            <h1>Dashboard</h1>
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
