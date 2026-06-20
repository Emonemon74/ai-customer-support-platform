import { api } from "../api/client";

export type Source = {
  document_id: number;
  chunk_index: number;
};

export type ChatResponse = {
  answer: string;
  sources: Source[];
};

export async function askQuestion(conversationId: number, question: string) {
  const response = await api.post<ChatResponse>("/api/v1/chat/ask", {
    conversation_id: conversationId,
    question,
  });

  return response.data;
}