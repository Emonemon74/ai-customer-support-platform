import { useState } from "react";

import { uploadDocument } from "../../services/document.service";

type DocumentUploadProps = {
  conversationId?: number;
  onCreateConversation?: (filename: string) => Promise<number>;
};

export function DocumentUpload({
  conversationId,
  onCreateConversation,
}: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false);

  async function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) return;

    try {
      setUploading(true);

      let targetConversationId = conversationId;

      if (!targetConversationId) {
        if (!onCreateConversation) {
          alert("Unable to create a conversation for this upload");
          return;
        }

        targetConversationId = await onCreateConversation(file.name);
      }

      await uploadDocument(file, targetConversationId);
      alert("Document uploaded successfully");
    } catch (error) {
      console.error(error);
      alert("Upload failed");
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
      {uploading ? "Uploading..." : "Upload PDF"}

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
