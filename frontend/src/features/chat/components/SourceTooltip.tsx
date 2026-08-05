import type { Source } from "../../../api/chatApi";

interface SourceTooltipProps {
  sources: Source[];
}

function formatSourceTitle(source: Source) {
  if (source.section_title) {
    return `${source.title || "Kaynak"} / ${source.section_title}`;
  }

  return source.title || source.document_id || "Kaynak";
}

function formatSourceMeta(source: Source) {
  const parts = [];

  if (source.category) parts.push(source.category);
  if (source.file_type) parts.push(source.file_type.toUpperCase());
  if (source.chunk_index) parts.push(`chunk ${source.chunk_index}`);

  return parts.join(" · ");
}

function SourceTooltip({ sources }: SourceTooltipProps) {
  const sourceLabel = sources.length === 1 ? "Kaynak" : "Kaynaklar";

  return (
    <details className="source-details">
      <summary className="source-summary">
        {sourceLabel} ({sources.length})
      </summary>

      <div className="source-list">
        {sources.map((source, index) => (
          <div
            className="source-item"
            key={`${source.document_id}-${index}`}
          >
            <span className="source-icon" aria-hidden="true">▣</span>

            <div className="source-copy">
              <strong>{formatSourceTitle(source)}</strong>
              <small>{formatSourceMeta(source)}</small>
            </div>
          </div>
        ))}
      </div>
    </details>
  );
}

export default SourceTooltip;
