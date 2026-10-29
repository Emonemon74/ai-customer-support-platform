import axios from "axios";
import { useState } from "react";
import toast from "react-hot-toast";

import { uploadDocument } from "../../services/document.service";

function uploadErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.message ?? error.response?.data?.detail;

    if (typeof detail === "string") return detail;
    if (error.response?.status === 413) return "File is too large";
    if (error.response?.status === 429) return "Too many uploads — try again shortly";
  }

  return "Upload failed";
}

type DocumentUploadProps = {
  conversationId?: number;
  onCreateConversation?: (filename: string) => Promise<number>;
  onUploaded?: () => void;
};

export function DocumentUpload({
  conversationId,
  onCreateConversation,
  onUploaded,
}: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  async function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) return;

    try {
      setUploading(true);
      setProgress(0);

      let targetConversationId = conversationId;

      if (!targetConversationId) {
        if (!onCreateConversation) {
          toast.error("Unable to create a conversation for this upload");
          return;
        }

        targetConversationId = await onCreateConversation(file.name);
      }

      await uploadDocument(file, targetConversationId, setProgress);
      onUploaded?.();
    } catch (error) {
      console.error(error);
      toast.error(uploadErrorMessage(error));
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  const disabled = uploading;

  return (
    <label
      className={`mt-4 block rounded-lg border border-dashed px-4 py-3 text-center text-sm ${
        disabled
          ? "cursor-not-allowed border-slate-200 text-slate-400"
          : "cursor-pointer border-slate-300 text-slate-600 hover:bg-slate-50"
      }`}
    >
      {uploading ? (
        <span className="block">
          {progress < 100 ? `Uploading… ${progress}%` : "Processing…"}
          <span className="mt-2 block h-1.5 overflow-hidden rounded-full bg-slate-200">
            <span
              className="block h-full bg-slate-900 transition-all"
              style={{ width: `${progress}%` }}
            />
          </span>
        </span>
      ) : (
        "Upload PDF"
      )}

      <input
        type="file"
        accept=".pdf"
        onChange={handleChange}
        disabled={disabled}
        className="hidden"
      />
    </label>
  );
}
