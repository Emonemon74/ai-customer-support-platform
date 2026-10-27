import { useRef, useState } from "react";
import toast from "react-hot-toast";

import { Menu } from "lucide-react";

import { ChatWindow } from "../../components/chat/ChatWindow";
import { Header } from "../../components/layout/Header";
import { Sidebar } from "../../components/layout/Sidebar";
import { streamQuestion, type Source } from "../../services/chat.service";
import {
  createConversation,
  renameConversation,
  type Conversation,
} from "../../services/conversation.service";
import { getMessages, type Message } from "../../services/message.service";

// Citations belong to the most recent assistant answer; restore them from the
// persisted messages so they survive a reload or conversation switch.
function latestSources(messages: Message[]): Source[] {
  const lastAssistant = [...messages]
    .reverse()
    .find((message) => message.role === "ASSISTANT");

  return lastAssistant?.sources ?? [];
}

export function DashboardPage() {
  const [selectedConversation, setSelectedConversation] =
    useState<Conversation>();

  const [messages, setMessages] = useState<Message[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [loading, setLoading] = useState(false);
  const abortRef = useRef<AbortController | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [sidebarRefreshKey, setSidebarRefreshKey] = useState(0);

  function handleNewChat() {
    setSelectedConversation(undefined);
    setMessages([]);
    setSources([]);
  }

  function handleConversationDeleted(conversationId: number) {
    if (selectedConversation?.id === conversationId) {
      handleNewChat();
    }
  }

  async function handleSelectConversation(conversation: Conversation) {
    setSelectedConversation(conversation);
    setSources([]);
    setIsSidebarOpen(false);

    try {
      const data = await getMessages(conversation.id);
      setMessages(data);
      setSources(latestSources(data));
    } catch (error) {
      console.error(error);
      toast.error("Failed to load messages");
    }
  }

  async function handleCreateConversationForUpload(filename: string) {
    const conversation = await createConversation(`Uploaded ${filename}`);
    const renamedConversation = await renameConversation(
      conversation.id,
      filename
    );

    setSelectedConversation(renamedConversation);
    setMessages([]);
    setSources([]);
    setSidebarRefreshKey((current) => current + 1);

    return renamedConversation.id;
  }

  function handleStop() {
    abortRef.current?.abort();
  }

  async function handleSend(question: string) {
    const controller = new AbortController();
    abortRef.current = controller;
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
        setSources,
        controller.signal
      );

      const updatedMessages = await getMessages(conversation.id);
      setMessages(updatedMessages);
      setSources(latestSources(updatedMessages));
    } catch (error) {
      if (controller.signal.aborted) {
        // User pressed Stop: keep the partial answer already on screen. The
        // server saves it too, so it is there when the conversation reloads.
        return;
      }

      console.error(error);
      toast.error("Failed to stream response");
      setMessages((current) =>
        current.map((message) =>
          message.role === "ASSISTANT" && message.content === ""
            ? {
                ...message,
                content:
                  "Sorry — something went wrong generating a response. Please try again.",
              }
            : message
        )
      );
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
          onCreateConversation={handleCreateConversationForUpload}
          onSelectConversation={handleSelectConversation}
          onConversationDeleted={handleConversationDeleted}
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
          onCreateConversation={handleCreateConversationForUpload}
          onSelectConversation={handleSelectConversation}
          onConversationDeleted={handleConversationDeleted}
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
          onStop={handleStop}
          sources={sources}
        />
      </div>
    </div>
  );
}
