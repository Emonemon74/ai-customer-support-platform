import { useCallback, useEffect, useRef, useState } from "react";

import { AlertTriangle, CheckCircle2, Loader2, RotateCw } from "lucide-react";

import {
  listDocuments,
  retryDocument,
  type Document,
  type DocumentStatus,
} from "../../services/document.service";

type DocumentListProps = {
  conversationId?: number;
  refreshKey?: number;
};

const IN_PROGRESS: DocumentStatus[] = ["QUEUED", "PROCESSING"];

function StatusBadge({ status }: { status: DocumentStatus }) {
  if (status === "READY") {
    return (
      <span className="flex items-center gap-1 text-xs text-emerald-600">
        <CheckCircle2 size={13} /> Ready
      </span>
    );
  }

  if (status === "FAILED") {
    return (
      <span className="flex items-center gap-1 text-xs text-red-600">
        <AlertTriangle size={13} /> Failed
      </span>
    );
  }

  return (
    <span className="flex items-center gap-1 text-xs text-slate-500">
      <Loader2 size={13} className="animate-spin" />
      {status === "QUEUED" ? "Queued" : "Processing"}
    </span>
  );
}

export function DocumentList({ conversationId, refreshKey }: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const timer = useRef<number | undefined>(undefined);

  const load = useCallback(async () => {
    if (!conversationId) {
      setDocuments([]);
      return;
    }

    try {
      setDocuments(await listDocuments(conversationId));
    } catch (error) {
      console.error(error);
    }
  }, [conversationId]);

  useEffect(() => {
    async function run() {
      await load();
    }

    void run();
  }, [load, refreshKey]);

  // Poll while any document is still being processed.
  useEffect(() => {
    const pending = documents.some((doc) => IN_PROGRESS.includes(doc.status));

    if (!pending) {
      return;
    }

    async function run() {
      await load();
    }

    timer.current = window.setTimeout(() => void run(), 2000);
    return () => window.clearTimeout(timer.current);
  }, [documents, load]);

  async function handleRetry(documentId: number) {
    if (!conversationId) return;

    try {
      await retryDocument(documentId, conversationId);
      await load();
    } catch (error) {
      console.error(error);
    }
  }

  if (!conversationId || documents.length === 0) {
    return null;
  }

  return (
    <div className="mt-4">
      <p className="mb-2 text-xs font-semibold uppercase text-slate-500">
        Documents
      </p>

      <div className="space-y-2">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="rounded-lg border border-slate-200 px-3 py-2"
          >
            <div className="flex items-center justify-between gap-2">
              <span
                className="min-w-0 flex-1 truncate text-sm text-slate-800"
                title={doc.filename}
              >
                {doc.filename}
              </span>

              <StatusBadge status={doc.status} />
            </div>

            {doc.status === "FAILED" && (
              <div className="mt-1 flex items-center justify-between gap-2">
                <span
                  className="min-w-0 flex-1 truncate text-xs text-red-500"
                  title={doc.failure_reason ?? undefined}
                >
                  {doc.failure_reason ?? "Processing failed"}
                </span>

                <button
                  type="button"
                  onClick={() => handleRetry(doc.id)}
                  className="flex items-center gap-1 rounded px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
                >
                  <RotateCw size={12} /> Retry
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
