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

function normalizeKeyPart(value?: string | null) {
  return value?.trim().toLocaleLowerCase("tr-TR") ?? "";
}

function getSourcePresentationKey(source: Source) {
  const sourceFileName = normalizeKeyPart(source.source_file_name);
  const title = normalizeKeyPart(source.title);
  const section = normalizeKeyPart(source.section_title);

  const documentIdentity = sourceFileName
    ? `file:${sourceFileName}`
    : `title:${title}`;

  return `${documentIdentity}::${section}`;
}

function getUniqueSources(sources: Source[]) {
  const seen = new Set<string>();

  return sources.filter((source) => {
    const key = getSourcePresentationKey(source);
    if (seen.has(key)) return false;

    seen.add(key);
    return true;
  });
}

function formatSourceMeta(source: Source) {
  const parts: string[] = [];
  const sourceFileName = source.source_file_name?.trim();
  const category = source.category?.trim();

  if (sourceFileName) parts.push(sourceFileName);
  if (category) parts.push(category);

  return parts.join(" · ");
}

function SourceTooltip({ sources }: SourceTooltipProps) {
  const uniqueSources = getUniqueSources(sources);
  const sourceLabel = uniqueSources.length === 1 ? "Kaynak" : "Kaynaklar";

  return (
    <details className="source-details">
      <summary className="source-summary">
        {sourceLabel} ({uniqueSources.length})
      </summary>

      <div className="source-list">
        {uniqueSources.map((source, index) => {
          const metadata = formatSourceMeta(source);

          return (
            <div
              className="source-item"
              key={`${getSourcePresentationKey(source)}-${index}`}
            >
              <span className="source-icon" aria-hidden="true">▣</span>

              <div className="source-copy">
                <strong>{formatSourceTitle(source)}</strong>
                {metadata && <small>{metadata}</small>}
              </div>
            </div>
          );
        })}
      </div>
    </details>
  );
}

export default SourceTooltip;
