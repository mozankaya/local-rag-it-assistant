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
  return (
    <div className="source-tooltip-wrapper">
      <button
        className="source-tooltip-trigger"
        type="button"
        aria-label="Kaynakları göster"
      >
        ⓘ Kaynak
      </button>

      <div className="source-tooltip-panel">
        <h4>Kaynaklar</h4>

        <div className="source-tooltip-list">
          {sources.map((source, index) => (
            <div
              className="source-tooltip-item"
              key={`${source.document_id}-${index}`}
            >
              <span className="source-icon">▣</span>

              <div>
                <strong>{formatSourceTitle(source)}</strong>
                <small>{formatSourceMeta(source)}</small>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default SourceTooltip;
