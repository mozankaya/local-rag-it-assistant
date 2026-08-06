import type { CurrentUserResponse } from "../../api/authApi";
import UserSidebar from "../../components/layout/UserSidebar";
import UserTopbar from "../../components/layout/UserTopbar";
import ChatBox from "./ChatBox";
import "./ChatPage.css";

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
  onNewChat,
  onGoToAdmin,
  onLogout,
}: ChatPageProps) {
  return (
    <div className="chat-page">
      <UserSidebar
        user={user}
        onNewChat={onNewChat}
        onGoToAdmin={onGoToAdmin}
        onLogout={onLogout}
      />

      <main className="chat-main">
        <UserTopbar user={user} />

        <section className="chat-content" aria-label="Sohbet">
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
