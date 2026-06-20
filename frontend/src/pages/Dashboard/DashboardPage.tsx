import { useState } from "react";

import { ChatWindow } from "../../components/chat/ChatWindow";
import { Header } from "../../components/layout/Header";
import { Sidebar } from "../../components/layout/Sidebar";
import { askQuestion } from "../../services/chat.service";
import type { Conversation } from "../../services/conversation.service";
import { getMessages, type Message } from "../../services/message.service";

export function DashboardPage() {
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation>();

  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSelectConversation(conversation: Conversation) {
    console.log("selected:", conversation);

    setSelectedConversation(conversation);

    try {
      const data = await getMessages(conversation.id);
      console.log("messages:", data);

      setMessages(data);
    } catch (error) {
      console.error(error);
    }
  }

  async function handleSend(question: string) {
    if (!selectedConversation) return;

    setLoading(true);

    try {
      await askQuestion(selectedConversation.id, question);

      const updatedMessages = await getMessages(selectedConversation.id);
      console.log("updated messages:", updatedMessages);

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