import { useState } from "react";

import { ChatWindow } from "../../components/chat/ChatWindow";
import { Header } from "../../components/layout/Header";
import { Sidebar } from "../../components/layout/Sidebar";
import { streamQuestion } from "../../services/chat.service";
import type { Conversation } from "../../services/conversation.service";
import { getMessages, type Message } from "../../services/message.service";

export function DashboardPage() {
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation>();

  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSelectConversation(conversation: Conversation) {
    setSelectedConversation(conversation);

    try {
      const data = await getMessages(conversation.id);
      setMessages(data);
    } catch (error) {
      console.error(error);
    }
  }

  async function handleSend(question: string) {
    if (!selectedConversation) return;

    setLoading(true);

    const userMessage: Message = {
      id: Date.now(),
      conversation_id: selectedConversation.id,
      role: "USER",
      content: question,
      created_at: new Date().toISOString(),
    };

    const assistantMessage: Message = {
      id: Date.now() + 1,
      conversation_id: selectedConversation.id,
      role: "ASSISTANT",
      content: "",
      created_at: new Date().toISOString(),
    };

    setMessages((current) => [
      ...current,
      userMessage,
      assistantMessage,
    ]);

    try {
      await streamQuestion(
        selectedConversation.id,
        question,
        (token) => {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantMessage.id
                ? {
                    ...message,
                    content: message.content + token,
                  }
                : message
            )
          );
        }
      );

      const updatedMessages = await getMessages(selectedConversation.id);
      setMessages(updatedMessages);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-screen">
      <Sidebar
        selectedConversationId={selectedConversation?.id}
        onSelectConversation={handleSelectConversation}
      />

      <div className="flex flex-1 flex-col">
        <Header />

        <ChatWindow
          title={selectedConversation?.title}
          messages={messages}
          disabled={!selectedConversation || loading}
          onSend={handleSend}
        />
      </div>
    </div>
  );
}