import { formatPercentage } from "./formatPercentage";

interface DistributionItem {
  key: string;
  label: string;
  count: number;
}

interface DistributionCardProps {
  title: string;
  subtitle: string;
  items: DistributionItem[];
  emptyText: string;
}

const numberFormatter = new Intl.NumberFormat("tr-TR");

function DistributionCard({
  title,
  subtitle,
  items,
  emptyText,
}: DistributionCardProps) {
  const total = items.reduce((sum, item) => sum + item.count, 0);
  const maxCount = Math.max(...items.map((item) => item.count), 1);

  return (
    <article className="admin-panel distribution-panel">
      <div className="admin-panel-header">
        <div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>
        <span className="admin-total-pill">{numberFormatter.format(total)}</span>
      </div>

      {items.length === 0 ? (
        <p className="admin-empty">{emptyText}</p>
      ) : (
        <div className="distribution-list">
          {items.map((item) => {
            const percentage = total > 0 ? (item.count / total) * 100 : 0;
            return (
              <div className="distribution-row" key={item.key}>
                <div className="distribution-meta">
                  <span>{item.label}</span>
                  <strong>{numberFormatter.format(item.count)} <small>{formatPercentage(percentage)}</small></strong>
                </div>
                <div className="distribution-track">
                  <span style={{ width: `${(item.count / maxCount) * 100}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </article>
  );
}

export default DistributionCard;
