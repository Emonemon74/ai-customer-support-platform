import { useState } from "react";
import toast from "react-hot-toast";

import { Menu } from "lucide-react";

import { ChatWindow } from "../../components/chat/ChatWindow";
import { Header } from "../../components/layout/Header";
import { Sidebar } from "../../components/layout/Sidebar";
import { streamQuestion, type Source } from "../../services/chat.service";
import {
  createConversation,
  type Conversation,
} from "../../services/conversation.service";
import { getMessages, type Message } from "../../services/message.service";

export function DashboardPage() {
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation>();

  const [messages, setMessages] = useState<Message[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);

  function handleNewChat() {
    setSelectedConversation(undefined);
    setMessages([]);
    setSources([]);
  }

  async function handleSelectConversation(conversation: Conversation) {
    setSelectedConversation(conversation);
    setSources([]);
    setIsSidebarOpen(false);

    try {
      const data = await getMessages(conversation.id);
      setMessages(data);
    } catch (error) {
      console.error(error);
      toast.error("Failed to load messages");
    }
  }

  async function handleSend(question: string) {
    setLoading(true);
    setSources([]);

    try {
      let conversation = selectedConversation;

      if (!conversation) {
        conversation = await createConversation(question);
        setSelectedConversation(conversation);
        setSidebarRefreshKey((current) => current + 1);
      }

      const userMessage: Message = {
        id: `temp-user-${Date.now()}` as unknown as number,
        conversation_id: conversation.id,
        role: "USER",
        content: question,
        created_at: new Date().toISOString(),
      };

      const assistantMessage: Message = {
        id: `temp-assistant-${Date.now()}` as unknown as number,
        conversation_id: conversation.id,
        role: "ASSISTANT",
        content: "",
        created_at: new Date().toISOString(),
      };

      setMessages((current) => [...current, userMessage, assistantMessage]);

      await streamQuestion(
        conversation.id,
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
        },
        (streamSources) => {
          setSources(streamSources);
        }
      );

      const updatedMessages = await getMessages(conversation.id);
      setMessages(updatedMessages);
    } catch (error) {
      console.error(error);
      toast.error("Failed to stream response");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative flex h-screen overflow-hidden">
      <div className="hidden md:block">
        <Sidebar
          selectedConversationId={selectedConversation?.id}
          refreshKey={sidebarRefreshKey}
          onNewChat={handleNewChat}
          onSelectConversation={handleSelectConversation}
        />
      </div>

      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      <div
        className={`fixed inset-y-0 left-0 z-50 transform transition-transform duration-300 md:hidden ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <Sidebar
          selectedConversationId={selectedConversation?.id}
          refreshKey={sidebarRefreshKey}
          onNewChat={handleNewChat}
          onSelectConversation={handleSelectConversation}
          onClose={() => setIsSidebarOpen(false)}
        />
      </div>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3 md:hidden">
          <button
            type="button"
            onClick={() => setIsSidebarOpen(true)}
            className="rounded-lg p-2 text-slate-700 hover:bg-slate-100"
            title="Open sidebar"
          >
            <Menu size={22} />
          </button>

          <p className="truncate text-sm font-semibold text-slate-900">
            {selectedConversation?.title || "New Chat"}
          </p>
        </div>

        <Header />

        <ChatWindow
          title={selectedConversation?.title || "New Chat"}
          messages={messages}
          disabled={loading}
          onSend={handleSend}
          sources={sources}
        />
      </div>
    </div>
  );
}