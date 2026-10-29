import { api } from "../api/client";

export type DocumentStatus =
  | "QUEUED"
  | "PROCESSING"
  | "READY"
  | "FAILED";

export type Document = {
  id: number;
  filename: string;
  file_type: string;
  file_path: string;
  status: DocumentStatus;
  failure_reason: string | null;
  uploaded_by: number;
  conversation_id: number;
  created_at: string;
  updated_at: string | null;
};

export async function uploadDocument(
  file: File,
  conversationId: number,
  onProgress?: (percent: number) => void
) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("conversation_id", String(conversationId));

  const response = await api.post<Document>(
    "/api/v1/documents/upload",
    formData,
    {
      headers: {
        "Content-Type": "multipart/form-data",
      },
      onUploadProgress: (event) => {
        if (event.total) {
          onProgress?.(Math.round((event.loaded / event.total) * 100));
        }
      },
    }
  );

  return response.data;
}

export async function listDocuments(conversationId: number) {
  const response = await api.get<Document[]>(
    `/api/v1/documents?conversation_id=${conversationId}`
  );

  return response.data;
}

export async function retryDocument(documentId: number, conversationId: number) {
  const response = await api.post<Document>(
    `/api/v1/documents/${documentId}/retry?conversation_id=${conversationId}`
  );

  return response.data;
}

export async function deleteDocument(documentId: number, conversationId: number) {
  await api.delete(
    `/api/v1/documents/${documentId}?conversation_id=${conversationId}`
  );
}
