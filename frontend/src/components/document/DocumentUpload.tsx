import { useState } from "react";

import { uploadDocument } from "../../services/document.service";

export function DocumentUpload() {
  const [uploading, setUploading] = useState(false);

  async function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) return;

    try {
      setUploading(true);
      await uploadDocument(file);
      alert("Document uploaded successfully");
    } catch (error) {
      console.error(error);
      alert("Upload failed");
    } finally {
      setUploading(false);
    }
  }

  return (
    <label className="mt-4 block cursor-pointer rounded-lg border border-dashed border-slate-300 px-4 py-3 text-center text-sm text-slate-600 hover:bg-slate-50">
      {uploading ? "Uploading..." : "Upload PDF"}

      <input
        type="file"
        accept=".pdf"
        onChange={handleChange}
        disabled={uploading}
        className="hidden"
      />
    </label>
  );
}