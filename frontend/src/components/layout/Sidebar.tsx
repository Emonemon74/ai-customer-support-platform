import { useEffect, useState } from "react";

import { DocumentUpload } from "../document/DocumentUpload";
import { Pencil, Trash2, Plus } from "lucide-react";

import {
  createConversation,
  getConversations,
  renameConversation,
  searchConversations,
  deleteConversation,
  type Conversation,
} from "../../services/conversation.service";

type SidebarProps = {
  selectedConversationId?: number;
  onSelectConversation: (conversation: Conversation) => void;
};

export function Sidebar({
  selectedConversationId,
  onSelectConversation,
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

  async function handleNewChat() {
    const question = prompt("Start your chat with a question:");

    if (!question) return;

    try {
      const conversation = await createConversation(question);

      setConversations((current) => [conversation, ...current]);

      onSelectConversation(conversation);
    } catch (error) {
      console.error(error);
    }
  }

  async function handleRename(conversation: Conversation) {
    const title = prompt(
      "Enter new conversation title:",
      conversation.title
    );

    if (!title || title.trim() === "") {
      return;
    }

    try {
      const updated = await renameConversation(
        conversation.id,
        title
      );

      setConversations((current) =>
        current.map((item) =>
          item.id === updated.id ? updated : item
        )
      );
    } catch (error) {
      console.error(error);
    }
  }

  async function handleDelete(conversation: Conversation) {
  const confirmed = confirm(
    `Delete "${conversation.title}"?`
  );

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

  useEffect(() => {
    async function load() {
      try {
        await loadConversations();
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return (
    <aside className="flex w-72 flex-col border-r border-slate-200 bg-white p-4">
      <button
        onClick={handleNewChat}
        className="w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800"
      >
       <span className="flex items-center justify-center gap-2">
        <Plus size={16} />
        New Chat
        </span>
      </button>

      <DocumentUpload />

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

        {loading && (
          <p className="text-sm text-slate-500">
            Loading...
          </p>
        )}

        {!loading && conversations.length === 0 && (
          <p className="text-sm text-slate-500">
            No conversations found.
          </p>
        )}

        <div className="space-y-2">
          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              className={`flex items-center gap-2 rounded-lg px-3 py-2 transition ${
                selectedConversationId === conversation.id
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-800 hover:bg-slate-200"
              }`}
            >
              <button
                onClick={() =>
                  onSelectConversation(conversation)
                }
                className="flex-1 text-left text-sm"
              >
                {conversation.title}
              </button>

              <button
                onClick={() =>
                  handleRename(conversation)
                }
                className="text-sm hover:scale-110"
                title="Rename"
              >
                <Pencil size={16} />
                <button
                    onClick={() => handleDelete(conversation)}
                    className="text-sm hover:scale-110"
                    title="Delete"
                >
                    <Trash2 size={16} />
                </button>
              </button>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}