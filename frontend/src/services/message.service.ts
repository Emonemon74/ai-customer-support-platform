import { api } from "../api/client";
import type { Source } from "./chat.service";

export type Message = {
  id: number;
  conversation_id: number;
  role: "USER" | "ASSISTANT";
  content: string;
  sources?: Source[] | null;
  created_at: string;
};

export async function getMessages(conversationId: number) {
  const response = await api.get<Message[]>(
    `/api/v1/conversations/${conversationId}/messages`
  );

  return response.data;
}