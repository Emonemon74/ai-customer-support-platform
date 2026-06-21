import type { Source } from "../../services/chat.service";

type Props = {
  sources: Source[];
};

export function SourceCitations({ sources }: Props) {
  if (sources.length === 0) return null;

  return (
    <div className="border-t border-slate-200 bg-white p-4">
      <p className="text-sm font-semibold text-slate-700">Sources</p>

      <div className="mt-2 flex flex-wrap gap-2">
        {sources.map((source, index) => (
          <span
            key={index}
            className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
          >
            Document {source.document_id} · Chunk {source.chunk_index}
          </span>
        ))}
      </div>
    </div>
  );
}