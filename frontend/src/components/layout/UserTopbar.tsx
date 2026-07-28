import type { CurrentUserResponse } from "../../api/authApi";

interface UserTopbarProps {
  user: CurrentUserResponse;
  onGoToAdmin: () => void;
  onLogout: () => void;
}

function UserTopbar({ user, onGoToAdmin, onLogout }: UserTopbarProps) {
  return (
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
          {user.full_name} · {user.role}
        </div>

        {user.role === "admin" && (
          <button
            className="admin-button"
            type="button"
            onClick={onGoToAdmin}
          >
            Admin Panel
          </button>
        )}

        <button
          className="logout-button"
          type="button"
          onClick={onLogout}
        >
          Çıkış
        </button>
      </div>
    </header>
  );
}

export default UserTopbar;
