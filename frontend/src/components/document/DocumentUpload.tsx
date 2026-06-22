import { useState } from "react";

import { uploadDocument } from "../../services/document.service";

type DocumentUploadProps = {
  conversationId?: number;
};

export function DocumentUpload({ conversationId }: DocumentUploadProps) {
  const [uploading, setUploading] = useState(false);

  async function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) return;

    if (!conversationId) {
      alert("Select a conversation before uploading a document");
      event.target.value = "";
      return;
    }

    try {
      setUploading(true);
      await uploadDocument(file, conversationId);
      alert("Document uploaded successfully");
    } catch (error) {
      console.error(error);
      alert("Upload failed");
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  }

  const disabled = uploading || !conversationId;

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
