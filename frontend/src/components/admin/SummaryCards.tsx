import type { DashboardSummary, FeedbackSummary } from "../../api/adminApi";

interface SummaryCardsProps {
  summary: DashboardSummary;
  feedback: FeedbackSummary;
}

const numberFormatter = new Intl.NumberFormat("tr-TR");

function SummaryCards({ summary, feedback }: SummaryCardsProps) {
  const satisfaction = feedback.total_feedback > 0
    ? Math.round((feedback.useful_feedback / feedback.total_feedback) * 100)
    : 0;

  const cards = [
    {
      label: "Toplam soru",
      value: numberFormatter.format(summary.total_questions),
      detail: `Bugün ${numberFormatter.format(summary.today_questions)} yeni soru`,
      icon: "?",
    },
    {
      label: "Toplam kullanıcı",
      value: numberFormatter.format(summary.total_users),
      detail: `${summary.admin_users} admin · ${summary.standard_users} kullanıcı`,
      icon: "◎",
    },
    {
      label: "Geri bildirim",
      value: numberFormatter.format(feedback.total_feedback),
      detail: `${feedback.useful_feedback} faydalı yanıt`,
      icon: "✓",
    },
    {
      label: "Memnuniyet oranı",
      value: `%${satisfaction}`,
      detail: `${feedback.not_useful_feedback} olumsuz bildirim`,
      icon: "↗",
    },
  ];

  return (
    <section className="admin-summary-grid" aria-label="Dashboard özeti">
      {cards.map((card) => (
        <article className="admin-summary-card" key={card.label}>
          <div className="admin-card-heading">
            <span>{card.label}</span>
            <i aria-hidden="true">{card.icon}</i>
          </div>
          <strong>{card.value}</strong>
          <small>{card.detail}</small>
        </article>
      ))}
    </section>
  );
}

export default SummaryCards;
