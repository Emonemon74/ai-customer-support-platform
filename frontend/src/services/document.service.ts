import { api } from "../api/client";

export type Document = {
  id: number;
  filename: string;
  file_type: string;
  file_path: string;
  uploaded_by: number;
};

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

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