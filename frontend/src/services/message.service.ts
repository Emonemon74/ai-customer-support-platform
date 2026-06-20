import { api } from "../api/client";

export type Message = {
  id: number;
  conversation_id: number;
  role: "USER" | "ASSISTANT";
  content: string;
  created_at: string;
};

export async function getMessages(conversationId: number) {
  const response = await api.get<Message[]>(
    `/api/v1/conversations/${conversationId}/messages`
  );

  return response.data;
}