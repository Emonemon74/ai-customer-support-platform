import { FileText } from "lucide-react";

import type { Source } from "../../services/chat.service";

type Props = {
  sources: Source[];
};

function label(source: Source) {
  const name = source.filename || `Document ${source.document_id}`;
  return source.page_number != null ? `${name} · p.${source.page_number}` : name;
}

export function SourceCitations({ sources }: Props) {
  const uniqueSources = sources.filter(
    (source, index, array) =>
      index ===
      array.findIndex(
        (item) =>
          item.document_id === source.document_id &&
          item.page_number === source.page_number &&
          item.filename === source.filename
      )
  );

  if (uniqueSources.length === 0) return null;

  return (
    <div className="mt-4 border-t border-slate-100 pt-3">
      <p className="text-xs font-semibold text-slate-600">
        Sources <span className="font-normal text-slate-400">· grounded in your documents</span>
      </p>

      <div className="mt-2 flex flex-wrap gap-2">
        {uniqueSources.map((source, index) => (
          <span
            key={`${source.document_id}-${source.page_number}-${index}`}
            className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700"
            title={label(source)}
          >
            <FileText size={14} />
            {label(source)}
          </span>
        ))}
      </div>
    </div>
  );
}
