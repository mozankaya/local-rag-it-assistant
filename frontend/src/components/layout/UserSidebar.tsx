interface UserSidebarProps {
  onQuickTopic: (question: string) => void;
}

const quickTopics = [
  {
    label: "VPN",
    question: "VPN bağlantısı kuramıyorum, ne yapmalıyım?",
  },
  {
    label: "Şifre",
    question: "Şifremi unuttum, nasıl sıfırlayabilirim?",
  },
  {
    label: "Outlook",
    question: "Outlook mail göndermiyor, ne yapmalıyım?",
  },
  {
    label: "Yazıcı",
    question: "Yazıcıdan çıktı alamıyorum, ne yapmalıyım?",
  },
  {
    label: "Donanım",
    question: "Donanım desteği talebi nasıl oluşturabilirim?",
  },
  {
    label: "Ağ",
    question: "İnternet bağlantım yok, ne yapmalıyım?",
  },
];

function UserSidebar({ onQuickTopic }: UserSidebarProps) {
  return (
    <aside className="sidebar">
      <div className="assistant-card">
        <div className="assistant-icon">IT</div>

        <h2>İZELTAŞ IT Danışma Asistanı</h2>
        <p>
          IT ile ilgili sorularınızda size hızlı ve doğru destek olmak için
          buradayım. Aşağıdaki konulardan birini seçebilir veya sorunuzu
          yazabilirsiniz.
        </p>
      </div>

      <div className="quick-topics">
        <h3>Hızlı Konular</h3>

        <div className="topic-grid">
          {quickTopics.map((topic) => (
            <button
              key={topic.label}
              type="button"
              onClick={() => onQuickTopic(topic.question)}
            >
              {topic.label}
            </button>
          ))}
        </div>
      </div>

      <div className="announcement-card">
        <h3>Duyurular</h3>
        <p>
          Sistem bakım ve destek süreçleri hakkında güncel bilgilendirmeler
          burada gösterilebilir.
        </p>
      </div>

      <div className="support-info">
        <p>Yardım ve destek için:</p>
        <strong>itdestek@izeltas.com</strong>
        <span>0232 XXX XX XX</span>
      </div>
    </aside>
  );
}

export default UserSidebar;
