import { useEffect, useState } from "react";

import { DocumentUpload } from "../document/DocumentUpload";
import { Pencil, Plus, Trash2, X } from "lucide-react";

import {
  deleteConversation,
  getConversations,
  renameConversation,
  searchConversations,
  type Conversation,
} from "../../services/conversation.service";

type SidebarProps = {
  selectedConversationId?: number;
  refreshKey?: number;
  onNewChat: () => void;
  onSelectConversation: (conversation: Conversation) => void;
  onClose?: () => void;
};

export function Sidebar({
  selectedConversationId,
  refreshKey,
  onNewChat,
  onSelectConversation,
  onClose,
}: SidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  async function loadConversations() {
    try {
      const data = await getConversations();
      setConversations(data);
    } catch (error) {
      console.error(error);
    }
  }

  async function handleSearch(value: string) {
    setSearch(value);

    try {
      if (!value.trim()) {
        await loadConversations();
        return;
      }

      const data = await searchConversations(value);
      setConversations(data);
    } catch (error) {
      console.error(error);
    }
  }

  function handleNewChat() {
    onNewChat();
    onClose?.();
  }

  async function handleRename(conversation: Conversation) {
    const title = prompt("Enter new conversation title:", conversation.title);

    if (!title || title.trim() === "") return;

    try {
      const updated = await renameConversation(conversation.id, title);

      setConversations((current) =>
        current.map((item) => (item.id === updated.id ? updated : item))
      );
    } catch (error) {
      console.error(error);
    }
  }

  async function handleDelete(conversation: Conversation) {
    const confirmed = confirm(`Delete "${conversation.title}"?`);

    if (!confirmed) return;

    try {
      await deleteConversation(conversation.id);

      setConversations((current) =>
        current.filter((item) => item.id !== conversation.id)
      );
    } catch (error) {
      console.error(error);
    }
  }

  function handleSelect(conversation: Conversation) {
    onSelectConversation(conversation);
    onClose?.();
  }

  useEffect(() => {
    async function load() {
      try {
        await loadConversations();
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [refreshKey]);

  return (
    <aside className="flex h-screen w-72 flex-col border-r border-slate-200 bg-white p-4 shadow-xl md:shadow-none">
      <div className="mb-4 flex items-center justify-between md:hidden">
        <h2 className="text-sm font-bold text-slate-900">Menu</h2>

        <button
          type="button"
          onClick={onClose}
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
          title="Close sidebar"
        >
          <X size={20} />
        </button>
      </div>

      <button
        onClick={handleNewChat}
        className="w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800"
      >
        <span className="flex items-center justify-center gap-2">
          <Plus size={16} />
          New Chat
        </span>
      </button>

      <DocumentUpload conversationId={selectedConversationId} />

      <input
        value={search}
        onChange={(event) => handleSearch(event.target.value)}
        placeholder="Search conversations..."
        className="mt-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-900"
      />

      <div className="mt-6 flex-1 overflow-y-auto">
        <p className="mb-3 text-xs font-semibold uppercase text-slate-500">
          Conversations
        </p>

        {loading && <p className="text-sm text-slate-500">Loading...</p>}

        {!loading && conversations.length === 0 && (
          <p className="text-sm text-slate-500">No conversations found.</p>
        )}

        <div className="space-y-2">
          {conversations.map((conversation) => {
            const isSelected = selectedConversationId === conversation.id;

            return (
              <div
                key={conversation.id}
                className={`group flex items-center gap-2 rounded-lg px-3 py-2 transition ${
                  isSelected
                    ? "bg-slate-900 text-white"
                    : "bg-slate-100 text-slate-800 hover:bg-slate-200"
                }`}
              >
                <button
                  onClick={() => handleSelect(conversation)}
                  className="min-w-0 flex-1 truncate text-left text-sm"
                  title={conversation.title}
                >
                  {conversation.title}
                </button>

                <button
                  onClick={() => handleRename(conversation)}
                  className={`rounded p-1 transition hover:scale-110 ${
                    isSelected
                      ? "text-slate-200 hover:bg-slate-800"
                      : "text-slate-500 hover:bg-slate-300 hover:text-slate-900"
                  }`}
                  title="Rename"
                >
                  <Pencil size={15} />
                </button>

                <button
                  onClick={() => handleDelete(conversation)}
                  className={`rounded p-1 transition hover:scale-110 ${
                    isSelected
                      ? "text-slate-200 hover:bg-slate-800"
                      : "text-slate-500 hover:bg-slate-300 hover:text-red-600"
                  }`}
                  title="Delete"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}
