import { api } from "../api/client";

export type Conversation = {
  id: number;
  title: string;
  user_id: number;
  created_at: string;
};

export async function getConversations() {
  const response = await api.get<Conversation[]>("/api/v1/conversations");
  return response.data;
}


export async function createConversation(question: string) {
  const response = await api.post<Conversation>("/api/v1/conversations", {
    question,
  });

  return response.data;
}


export async function searchConversations(query: string) {
  const response = await api.get<Conversation[]>(
    `/api/v1/conversations/search?q=${query}`
  );

  return response.data;
}


export async function renameConversation(
  conversationId: number,
  title: string
) {
  const response = await api.patch<Conversation>(
    `/api/v1/conversations/${conversationId}`,
    { title }
  );

  return response.data;
}


export async function deleteConversation(conversationId: number) {
  await api.delete(`/api/v1/conversations/${conversationId}`);
}