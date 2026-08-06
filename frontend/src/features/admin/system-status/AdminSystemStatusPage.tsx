import { useEffect, useRef, useState } from "react";
import {
  AdminApiError,
  getSystemStatus,
  type SystemStatusResponse,
} from "../../../api/adminApi";
import type { CurrentUserResponse } from "../../../api/authApi";
import AdminLayout from "../shared/AdminLayout";
import "./AdminSystemStatusPage.css";

interface AdminSystemStatusPageProps {
  user: CurrentUserResponse;
  onGoToDashboard: () => void;
  onGoToReviewItems: () => void;
  onGoToUsers: () => void;
  onGoToDocuments: () => void;
  onGoToSystemStatus: () => void;
  onGoToChat: () => void;
  onLogout: () => void;
}

const services: Array<{
  key: keyof SystemStatusResponse["services"];
  name: string;
  icon: string;
}> = [
  { key: "api", name: "Backend API", icon: "↔" },
  { key: "database", name: "PostgreSQL", icon: "▤" },
  { key: "n8n", name: "n8n", icon: "⌘" },
  { key: "ollama", name: "Ollama", icon: "◈" },
];

function AdminSystemStatusPage({
  user,
  onGoToDashboard,
  onGoToReviewItems,
  onGoToUsers,
  onGoToDocuments,
  onGoToSystemStatus,
  onGoToChat,
  onLogout,
}: AdminSystemStatusPageProps) {
  const [systemStatus, setSystemStatus] = useState<SystemStatusResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState("");
  const isMountedRef = useRef(false);
  const requestInFlightRef = useRef(false);

  useEffect(() => {
    isMountedRef.current = true;

    async function loadInitialSystemStatus() {
      try {
        const data = await getSystemStatus();
        if (isMountedRef.current) setSystemStatus(data);
      } catch (requestError) {
        if (!isMountedRef.current) return;

        if (requestError instanceof AdminApiError && requestError.status === 401) {
          onLogout();
          return;
        }

        if (requestError instanceof AdminApiError && requestError.status === 403) {
          onGoToChat();
          return;
        }

        setError("Sistem durumu alınamadı.");
      } finally {
        requestInFlightRef.current = false;
        if (isMountedRef.current) setIsLoading(false);
      }
    }

    if (!requestInFlightRef.current) {
      requestInFlightRef.current = true;
      void loadInitialSystemStatus();
    }

    return () => {
      isMountedRef.current = false;
    };
  }, [onGoToChat, onLogout]);

  async function handleRefresh() {
    if (requestInFlightRef.current) return;

    requestInFlightRef.current = true;
    setError("");
    setIsRefreshing(true);

    try {
      setSystemStatus(await getSystemStatus());
    } catch (requestError) {
      if (requestError instanceof AdminApiError && requestError.status === 401) {
        onLogout();
        return;
      }

      if (requestError instanceof AdminApiError && requestError.status === 403) {
        onGoToChat();
        return;
      }

      setError("Sistem durumu alınamadı.");
    } finally {
      requestInFlightRef.current = false;
      setIsRefreshing(false);
    }
  }

  const isBusy = isLoading || isRefreshing;

  return (
    <AdminLayout
      user={user}
      activePage="system-status"
      pageTitle="Sistem Durumu"
      pageDescription="Sistemin temel servislerinin erişilebilirlik durumunu görüntüleyin."
      onGoToDashboard={onGoToDashboard}
      onGoToReviewItems={onGoToReviewItems}
      onGoToUsers={onGoToUsers}
      onGoToDocuments={onGoToDocuments}
      onGoToSystemStatus={onGoToSystemStatus}
      onGoToChat={onGoToChat}
      onLogout={onLogout}
    >
      <div className="admin-content system-status-content">
        <div className="system-status-actions">
          <button
            className="system-status-refresh"
            type="button"
            disabled={isBusy}
            aria-busy={isBusy}
            onClick={() => void handleRefresh()}
          >
            {isRefreshing && <span aria-hidden="true" />}
            {isRefreshing ? "Yenileniyor..." : "Yenile"}
          </button>
        </div>

        {isLoading && (
          <div className="admin-loading" role="status">
            <span />
            Sistem durumu yükleniyor...
          </div>
        )}

        {error && <div className="admin-error" role="alert">{error}</div>}

        {!isLoading && systemStatus && (
          <>
            <section
              className={`system-overall-status ${systemStatus.overall_status}`}
              aria-label="Genel sistem durumu"
            >
              <span className="system-overall-icon" aria-hidden="true">
                {systemStatus.overall_status === "healthy" ? "✓" : "!"}
              </span>
              <div>
                <small>Genel durum</small>
                <strong>
                  {systemStatus.overall_status === "healthy"
                    ? "Tüm sistemler çalışıyor"
                    : "Bazı servislerde sorun var"}
                </strong>
              </div>
            </section>

            <section className="system-service-grid" aria-label="Servis durumları">
              {services.map((service) => {
                const detail = systemStatus.services[service.key];

                return (
                  <article className="system-service-card" key={service.key}>
                    <div className="system-service-heading">
                      <span className="system-service-icon" aria-hidden="true">
                        {service.icon}
                      </span>
                      <h2>{service.name}</h2>
                    </div>
                    <span className={`system-service-badge ${detail.status}`}>
                      {detail.status === "healthy" ? "Çalışıyor" : "Erişilemiyor"}
                    </span>
                    <p>{detail.message}</p>
                  </article>
                );
              })}
            </section>
          </>
        )}
      </div>
    </AdminLayout>
  );
}

export default AdminSystemStatusPage;
