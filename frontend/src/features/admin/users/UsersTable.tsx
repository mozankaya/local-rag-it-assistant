import { useEffect, useState } from "react";
import type { AdminUser } from "../../../api/adminUsersApi";
import type { UserRole } from "../../../types/user";
import { formatDate } from "../../../utils/formatDate";

interface UsersTableProps {
  users: AdminUser[];
  currentUserId: number;
  pendingAction: string;
  onRoleChange: (user: AdminUser, role: UserRole) => void;
  onStatusChange: (user: AdminUser) => void;
  onDelete: (user: AdminUser) => void;
}

const RETENTION_DAYS = 30;
const RETENTION_DURATION_MS = RETENTION_DAYS * 24 * 60 * 60 * 1000;
const TIMER_INTERVAL_MS = 60 * 1000;

function getRetentionExpiry(deactivatedAt: string | null): number | null {
  if (!deactivatedAt) return null;

  const deactivatedAtMs = new Date(deactivatedAt).getTime();
  if (Number.isNaN(deactivatedAtMs)) return null;

  return deactivatedAtMs + RETENTION_DURATION_MS;
}

function formatRemainingTime(remainingMs: number): string {
  const dayMs = 24 * 60 * 60 * 1000;
  const hourMs = 60 * 60 * 1000;
  const minuteMs = 60 * 1000;

  if (remainingMs >= dayMs) {
    return `${Math.ceil(remainingMs / dayMs)} gün kaldı`;
  }

  if (remainingMs >= hourMs) {
    return `${Math.ceil(remainingMs / hourMs)} saat kaldı`;
  }

  return `${Math.ceil(remainingMs / minuteMs)} dakika kaldı`;
}

function UsersTable({
  users,
  currentUserId,
  pendingAction,
  onRoleChange,
  onStatusChange,
  onDelete,
}: UsersTableProps) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const timerId = window.setInterval(() => setNow(Date.now()), TIMER_INTERVAL_MS);
    return () => window.clearInterval(timerId);
  }, []);

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
            const isDeletePending = pendingAction === `${user.id}:delete`;
            const retentionExpiry = getRetentionExpiry(user.deactivated_at);
            const isRetentionExpired = retentionExpiry !== null && now >= retentionExpiry;
            const canDelete = !user.is_active
              && isRetentionExpired
              && !isCurrentUser
              && !pendingAction;

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
                  <div className="user-status-cell">
                    <span className={`user-status-badge ${user.is_active ? "active" : "inactive"}`}>
                      {user.is_active ? "Aktif" : "Pasif"}
                    </span>

                    {!user.is_active && (
                      <div className="user-retention-info">
                        {retentionExpiry === null ? (
                          <small className="retention-status missing">
                            Pasifleştirme tarihi bulunamadı.
                          </small>
                        ) : (
                          <>
                            <small>
                              <strong>Pasifleştirildi:</strong> {formatDate(user.deactivated_at)}
                            </small>
                            <small>
                              <strong>Kalıcı silme tarihi:</strong>{" "}
                              {formatDate(new Date(retentionExpiry).toISOString())}
                            </small>
                            <small className={`retention-status ${isRetentionExpired ? "eligible" : "waiting"}`}>
                              {isRetentionExpired
                                ? "Kalıcı silinebilir"
                                : formatRemainingTime(retentionExpiry - now)}
                            </small>
                          </>
                        )}
                      </div>
                    )}
                  </div>
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
                    {!user.is_active && (
                      <button
                        className="user-permanent-delete"
                        type="button"
                        disabled={!canDelete}
                        aria-busy={isDeletePending}
                        onClick={() => onDelete(user)}
                      >
                        {isDeletePending ? "Siliniyor..." : "Kalıcı Sil"}
                      </button>
                    )}
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
