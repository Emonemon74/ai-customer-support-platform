import { useState } from "react";

import { ChatWindow } from "../../components/chat/ChatWindow";
import { Header } from "../../components/layout/Header";
import { Sidebar } from "../../components/layout/Sidebar";
import { askQuestion, type Source } from "../../services/chat.service";
import type { Conversation } from "../../services/conversation.service";
import { getMessages, type Message } from "../../services/message.service";

export function DashboardPage() {
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation>();

  const [messages, setMessages] = useState<Message[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSelectConversation(conversation: Conversation) {
    setSelectedConversation(conversation);
    setSources([]);

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

    try {
      const response = await askQuestion(
        selectedConversation.id,
        question
      );

      setSources(response.sources);

      const updatedMessages = await getMessages(
        selectedConversation.id
      );

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
          sources={sources}
        />
      </div>
    </div>
  );
}