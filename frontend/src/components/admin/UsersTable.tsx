import type { AdminUser, UserRole } from "../../api/adminUsersApi";

interface UsersTableProps {
  users: AdminUser[];
  currentUserId: number;
  pendingAction: string;
  onRoleChange: (user: AdminUser, role: UserRole) => void;
  onStatusChange: (user: AdminUser) => void;
}

function formatDate(value?: string | null) {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("tr-TR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function UsersTable({
  users,
  currentUserId,
  pendingAction,
  onRoleChange,
  onStatusChange,
}: UsersTableProps) {
  if (users.length === 0) {
    return <p className="admin-empty">Aramanıza uygun kullanıcı bulunamadı.</p>;
  }

  return (
    <div className="admin-users-table-wrap">
      <table className="admin-users-table">
        <thead>
          <tr>
            <th>Ad soyad</th>
            <th>E-posta</th>
            <th>Rol</th>
            <th>Durum</th>
            <th>Oluşturulma tarihi</th>
            <th>İşlemler</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => {
            const isCurrentUser = user.id === currentUserId;
            const isRolePending = pendingAction === `${user.id}:role`;
            const isStatusPending = pendingAction === `${user.id}:status`;

            return (
              <tr className={isCurrentUser ? "current-user-row" : ""} key={user.id}>
                <td>
                  <div className="table-user-name">
                    <span>{user.full_name.slice(0, 1).toLocaleUpperCase("tr-TR")}</span>
                    <strong>{user.full_name}</strong>
                    {isCurrentUser && <span className="current-user-badge">Siz</span>}
                  </div>
                </td>
                <td className="table-user-email">{user.email}</td>
                <td>
                  <span className={`user-role-badge role-${user.role}`}>
                    {user.role === "admin" ? "Admin" : "Kullanıcı"}
                  </span>
                </td>
                <td>
                  <span className={`user-status-badge ${user.is_active ? "active" : "inactive"}`}>
                    {user.is_active ? "Aktif" : "Pasif"}
                  </span>
                </td>
                <td className="table-user-date">{formatDate(user.created_at)}</td>
                <td>
                  <div className={`user-row-actions ${isCurrentUser ? "self-account-actions" : ""}`}>
                    <label>
                      <span className="sr-only">{user.full_name} rolü</span>
                      <select
                        value={user.role}
                        disabled={isCurrentUser || Boolean(pendingAction)}
                        aria-busy={isRolePending}
                        onChange={(event) => onRoleChange(user, event.target.value as UserRole)}
                      >
                        <option value="user">Kullanıcı</option>
                        <option value="admin">Admin</option>
                      </select>
                    </label>

                    <button
                      className={`user-status-toggle ${user.is_active ? "deactivate" : "activate"}`}
                      type="button"
                      disabled={isCurrentUser || Boolean(pendingAction)}
                      aria-busy={isStatusPending}
                      onClick={() => onStatusChange(user)}
                    >
                      {isStatusPending
                        ? "Güncelleniyor..."
                        : user.is_active
                          ? "Pasif yap"
                          : "Aktif yap"}
                    </button>
                    {isRolePending && <small className="row-action-loading">Kaydediliyor...</small>}
                    {isCurrentUser && (
                      <small className="self-account-note">
                        Kendi hesabınız buradan değiştirilemez.
                      </small>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default UsersTable;
