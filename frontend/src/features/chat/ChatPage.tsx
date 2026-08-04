import type { CurrentUserResponse } from "../../api/authApi";
import UserSidebar from "../../components/layout/UserSidebar";
import UserTopbar from "../../components/layout/UserTopbar";
import ChatBox from "./ChatBox";

interface ChatPageProps {
  user: CurrentUserResponse;
  quickQuestion: {
    id: number;
    question: string;
  } | null;
  resetSignal: number;
  onQuickTopic: (question: string) => void;
  onNewChat: () => void;
  onGoToAdmin: () => void;
  onLogout: () => void;
}

function ChatPage({
  user,
  quickQuestion,
  resetSignal,
  onQuickTopic,
  onNewChat,
  onGoToAdmin,
  onLogout,
}: ChatPageProps) {
  return (
    <div className="app-shell">
      <UserTopbar
        user={user}
        onGoToAdmin={onGoToAdmin}
        onLogout={onLogout}
      />

      <main className="dashboard-layout">
        <UserSidebar onQuickTopic={onQuickTopic} />

        <section className="chat-panel">
          <div className="chat-panel-header">
            <div>
              <h2>Sohbet</h2>
              <span>IT destek dokümanlarına göre cevap üretir</span>
            </div>

            <button
              className="new-chat-button"
              type="button"
              onClick={onNewChat}
            >
              Yeni Sohbet
            </button>
          </div>

          <ChatBox
            key={resetSignal}
            quickQuestion={quickQuestion}
            onUnauthorized={onLogout}
          />
        </section>
      </main>
    </div>
  );
}

export default ChatPage;
