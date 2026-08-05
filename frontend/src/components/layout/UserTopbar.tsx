import type { CurrentUserResponse } from "../../api/authApi";

interface UserTopbarProps {
  user: CurrentUserResponse;
}

function UserTopbar({ user }: UserTopbarProps) {
  const roleLabel = user.role === "admin" ? "Yönetici" : "Kullanıcı";

  return (
    <header className="user-topbar">
      <div className="user-topbar-heading">
        <span>İç destek</span>
        <h1>IT Danışma Asistanı</h1>
      </div>

      <div className="user-identity">
        <strong>{user.full_name}</strong>
        <span>{roleLabel}</span>
      </div>
    </header>
  );
}

export default UserTopbar;
