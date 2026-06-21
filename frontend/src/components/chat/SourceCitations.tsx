import { FileText } from "lucide-react";

import type { Source } from "../../services/chat.service";

type Props = {
  sources: Source[];
};

export function SourceCitations({ sources }: Props) {
  const uniqueSources = sources.filter(
    (source, index, array) =>
      index ===
      array.findIndex(
        (item) =>
          item.document_id === source.document_id &&
          item.chunk_index === source.chunk_index &&
          item.filename === source.filename
      )
  );

  if (uniqueSources.length === 0) return null;

  return (
    <div className="border-t border-slate-200 bg-white p-4">
      <p className="text-sm font-semibold text-slate-700">Sources</p>

      <div className="mt-2 flex flex-wrap gap-2">
        {uniqueSources.map((source, index) => (
          <span
            key={`${source.document_id}-${source.chunk_index}-${index}`}
            className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700"
            title={`Document ID: ${source.document_id}`}
          >
            <FileText size={14} />
            {source.filename || `Document ${source.document_id}`} · Chunk{" "}
            {source.chunk_index}
          </span>
        ))}
      </div>
    </div>
  );
}