import { api } from "../api/client";

export type Document = {
  id: number;
  filename: string;
  file_type: string;
  file_path: string;
  uploaded_by: number;
  conversation_id: number;
};

export async function uploadDocument(file: File, conversationId: number) {
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
    }
  );

  return response.data;
}
