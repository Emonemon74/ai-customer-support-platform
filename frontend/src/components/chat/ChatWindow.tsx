import { ChatInput } from "./ChatInput";
import type { Message } from "../../services/message.service";

type ChatWindowProps = {
  title?: string;
  messages: Message[];
  disabled?: boolean;
  onSend: (question: string) => Promise<void>;
};

export function ChatWindow({
  title,
  messages,
  disabled,
  onSend,
}: ChatWindowProps) {
  return (
    <main className="flex flex-1 flex-col bg-slate-100">
      <div className="border-b border-slate-200 bg-white px-6 py-4">
        <h2 className="text-lg font-bold text-slate-900">
          {title || "Select a conversation"}
        </h2>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center">
            <div>
              <h3 className="text-2xl font-bold text-slate-900">
                Welcome to your AI workspace
              </h3>
              <p className="mt-2 text-slate-600">
                Select a conversation to view messages.
              </p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === "USER" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-2xl rounded-2xl px-4 py-3 text-sm ${
                  message.role === "USER"
                    ? "bg-slate-900 text-white"
                    : "bg-white text-slate-800 shadow-sm"
                }`}
              >
                {message.content}
              </div>
            </div>
          ))
        )}
      </div>

      <ChatInput disabled={disabled} onSend={onSend} />
    </main>
  );
}