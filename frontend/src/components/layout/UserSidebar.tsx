import type { CurrentUserResponse } from "../../api/authApi";
import izeltasLogo from "../../assets/izeltas-logo.png";
import "./UserSidebar.css";

interface UserSidebarProps {
  user: CurrentUserResponse;
  onNewChat: () => void;
  onGoToAdmin: () => void;
  onLogout: () => void;
}

function UserSidebar({
  user,
  onNewChat,
  onGoToAdmin,
  onLogout,
}: UserSidebarProps) {
  return (
    <aside className="user-sidebar">
      <div className="user-sidebar-brand">
        <img
          className="user-sidebar-logo"
          src={izeltasLogo}
          alt="İzeltaş"
        />
        <span>IT DANIŞMA ASİSTANI</span>
      </div>

      <button
        className="user-sidebar-new-chat"
        type="button"
        onClick={onNewChat}
      >
        <span aria-hidden="true">＋</span>
        Yeni Sohbet
      </button>

      <nav className="user-sidebar-nav" aria-label="Ana navigasyon">
        <span className="user-sidebar-nav-item active" aria-current="page">
          <span aria-hidden="true">◇</span>
          Sohbet
        </span>

        {user.role === "admin" && (
          <button
            className="user-sidebar-nav-item"
            type="button"
            onClick={onGoToAdmin}
          >
            <span aria-hidden="true">▤</span>
            Yönetim
          </button>
        )}
      </nav>

      <button
        className="user-sidebar-logout"
        type="button"
        onClick={onLogout}
      >
        <span aria-hidden="true">↪</span>
        Çıkış Yap
      </button>
    </aside>
  );
}

export default UserSidebar;
