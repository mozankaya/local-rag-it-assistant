import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  AdminUsersApiError,
  getAdminUsers,
  updateAdminUserRole,
  updateAdminUserStatus,
  type AdminUser,
} from "../../../api/adminUsersApi";
import type { CurrentUserResponse } from "../../../api/authApi";
import type { UserRole } from "../../../types/user";
import AdminLayout from "../shared/AdminLayout";
import UserCreateForm from "./UserCreateForm";
import UsersTable from "./UsersTable";
import "../../../components/admin/admin.css";

interface AdminUsersPageProps {
  user: CurrentUserResponse;
  onGoToDashboard: () => void;
  onGoToReviewItems: () => void;
  onGoToUsers: () => void;
  onGoToDocuments: () => void;
  onGoToChat: () => void;
  onLogout: () => void;
}

const PAGE_SIZE = 10;

function AdminUsersPage({
  user,
  onGoToDashboard,
  onGoToReviewItems,
  onGoToUsers,
  onGoToDocuments,
  onGoToChat,
  onLogout,
}: AdminUsersPageProps) {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [nextOffset, setNextOffset] = useState(PAGE_SIZE);
  const [hasMore, setHasMore] = useState(false);
  const [searchInput, setSearchInput] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [pendingAction, setPendingAction] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let isCancelled = false;

    async function loadUsers() {
      try {
        const data = await getAdminUsers(PAGE_SIZE, 0, activeSearch);
        if (isCancelled) return;

        setUsers(data.items);
        setTotal(data.total);
        setNextOffset(data.offset + PAGE_SIZE);
        setHasMore(data.has_more);
      } catch (requestError) {
        if (isCancelled) return;

        if (requestError instanceof AdminUsersApiError && requestError.status === 401) {
          onLogout();
          return;
        }
        if (requestError instanceof AdminUsersApiError && requestError.status === 403) {
          onGoToChat();
          return;
        }

        setError("Kullanıcılar şu anda yüklenemiyor. Lütfen tekrar deneyin.");
      } finally {
        if (!isCancelled) setIsLoading(false);
      }
    }

    void loadUsers();

    return () => {
      isCancelled = true;
    };
  }, [activeSearch, onGoToChat, onLogout, refreshKey]);

  function refreshUsers(resetSearch = false) {
    setError("");
    setUsers([]);
    setIsLoading(true);

    if (resetSearch) {
      setSearchInput("");
      if (activeSearch) {
        setActiveSearch("");
        return;
      }
    }

    setRefreshKey((current) => current + 1);
  }

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextSearch = searchInput.trim();

    setSuccess("");
    setError("");
    setUsers([]);
    setIsLoading(true);

    if (nextSearch === activeSearch) {
      setRefreshKey((current) => current + 1);
    } else {
      setActiveSearch(nextSearch);
    }
  }

  async function handleLoadMore() {
    if (isLoadingMore || !hasMore) return;

    setError("");
    setIsLoadingMore(true);

    try {
      const data = await getAdminUsers(PAGE_SIZE, nextOffset, activeSearch);
      setUsers((current) => [...current, ...data.items]);
      setTotal(data.total);
      setNextOffset(data.offset + PAGE_SIZE);
      setHasMore(data.has_more);
    } catch (requestError) {
      if (requestError instanceof AdminUsersApiError && requestError.status === 401) {
        onLogout();
        return;
      }
      if (requestError instanceof AdminUsersApiError && requestError.status === 403) {
        onGoToChat();
        return;
      }

      setError("Yeni kullanıcılar yüklenemedi. Lütfen tekrar deneyin.");
    } finally {
      setIsLoadingMore(false);
    }
  }

  async function handleRoleChange(targetUser: AdminUser, role: UserRole) {
    if (targetUser.id === user.id || targetUser.role === role || pendingAction) return;

    setError("");
    setSuccess("");
    setPendingAction(`${targetUser.id}:role`);

    try {
      const updatedUser = await updateAdminUserRole(targetUser.id, role);
      setUsers((current) => current.map((item) => (
        item.id === updatedUser.id ? updatedUser : item
      )));
      setSuccess(`${updatedUser.full_name} kullanıcısının rolü güncellendi.`);
    } catch (requestError) {
      if (requestError instanceof AdminUsersApiError && requestError.status === 401) {
        onLogout();
        return;
      }
      if (requestError instanceof AdminUsersApiError && requestError.status === 403) {
        onGoToChat();
        return;
      }

      setError("Kullanıcı rolü güncellenemedi. Lütfen tekrar deneyin.");
    } finally {
      setPendingAction("");
    }
  }

  async function handleStatusChange(targetUser: AdminUser) {
    if (targetUser.id === user.id || pendingAction) return;

    setError("");
    setSuccess("");
    setPendingAction(`${targetUser.id}:status`);

    try {
      const updatedUser = await updateAdminUserStatus(
        targetUser.id,
        !targetUser.is_active,
      );
      setUsers((current) => current.map((item) => (
        item.id === updatedUser.id ? updatedUser : item
      )));
      setSuccess(
        `${updatedUser.full_name} kullanıcısı ${updatedUser.is_active ? "aktif" : "pasif"} yapıldı.`,
      );
    } catch (requestError) {
      if (requestError instanceof AdminUsersApiError && requestError.status === 401) {
        onLogout();
        return;
      }
      if (requestError instanceof AdminUsersApiError && requestError.status === 403) {
        onGoToChat();
        return;
      }

      setError("Kullanıcı durumu güncellenemedi. Lütfen tekrar deneyin.");
    } finally {
      setPendingAction("");
    }
  }

  return (
    <AdminLayout
      user={user}
      activePage="users"
      pageTitle="Kullanıcı Yönetimi"
      pageDescription="Kullanıcı hesaplarını, rollerini ve erişim durumlarını yönetin"
      onGoToDashboard={onGoToDashboard}
      onGoToReviewItems={onGoToReviewItems}
      onGoToUsers={onGoToUsers}
      onGoToDocuments={onGoToDocuments}
      onGoToChat={onGoToChat}
      onLogout={onLogout}
    >
      <div className="admin-content admin-users-content">
        <UserCreateForm
          onCreated={() => refreshUsers(true)}
          onUnauthorized={onLogout}
          onForbidden={onGoToChat}
        />

        <article className="admin-panel users-list-panel">
          <div className="admin-panel-header users-list-header">
            <div>
              <h2>Kullanıcılar</h2>
              <p>Sistemde kayıtlı kullanıcılar ve erişim yetkileri</p>
            </div>
            <span className="admin-total-pill">{total} kullanıcı</span>
          </div>

          <form className="admin-user-search" onSubmit={handleSearch}>
            <input
              type="search"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Ad soyad veya e-posta ara..."
              aria-label="Kullanıcı ara"
            />
            <button type="submit" disabled={isLoading}>Ara</button>
          </form>

          {success && <div className="admin-success user-list-message" role="status">{success}</div>}
          {error && <div className="admin-form-error user-list-message" role="alert">{error}</div>}

          {isLoading ? (
            <div className="admin-loading users-loading" role="status">
              <span />
              Kullanıcılar yükleniyor...
            </div>
          ) : (
            <UsersTable
              users={users}
              currentUserId={user.id}
              pendingAction={pendingAction}
              onRoleChange={handleRoleChange}
              onStatusChange={handleStatusChange}
            />
          )}

          {hasMore && !isLoading && (
            <button
              className="load-more-button"
              type="button"
              onClick={handleLoadMore}
              disabled={isLoadingMore}
              aria-busy={isLoadingMore}
            >
              {isLoadingMore ? "Yükleniyor..." : "Daha fazla göster"}
            </button>
          )}
        </article>
      </div>
    </AdminLayout>
  );
}

export default AdminUsersPage;
