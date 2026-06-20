import { useEffect, useState } from "react";

import {
  createConversation,
  type Conversation,
  getConversations,
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

  async function loadConversations() {
    const data = await getConversations();
    setConversations(data);
  }

  async function handleNewChat() {
    const question = prompt("Start your chat with a question:");

    if (!question) return;

    const conversation = await createConversation(question);

    setConversations((current) => [conversation, ...current]);
    onSelectConversation(conversation);
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
    <aside className="w-72 border-r border-slate-200 bg-white p-4">
      <button
        onClick={handleNewChat}
        className="w-full rounded-lg bg-slate-900 px-4 py-3 text-sm font-semibold text-white"
      >
        + New Chat
      </button>

      <div className="mt-6">
        <p className="text-xs font-semibold uppercase text-slate-500">
          Conversations
        </p>

        <div className="mt-3 space-y-2">
          {loading && <p className="text-sm text-slate-500">Loading...</p>}

          {!loading && conversations.length === 0 && (
            <p className="text-sm text-slate-500">No conversations yet.</p>
          )}

          {conversations.map((conversation) => (
            <button
              key={conversation.id}
              onClick={() => onSelectConversation(conversation)}
              className={`w-full rounded-lg px-3 py-2 text-left text-sm ${
                selectedConversationId === conversation.id
                  ? "bg-slate-900 text-white"
                  : "bg-slate-100 text-slate-800 hover:bg-slate-200"
              }`}
            >
              {conversation.title}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}