import { Square } from "lucide-react";
import { useState } from "react";

type ChatInputProps = {
  disabled?: boolean;
  onSend: (question: string) => Promise<void>;
  onStop?: () => void;
};

export function ChatInput({ disabled, onSend, onStop }: ChatInputProps) {
  const [question, setQuestion] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmed = question.trim();
    if (!trimmed || disabled) return;

    // Clear straight away so the box is free while the answer streams in.
    setQuestion("");
    await onSend(trimmed);
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-slate-200 bg-white p-3 sm:p-4"
    >
      <div className="flex gap-3">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={disabled}
          placeholder="Ask a question..."
          aria-label="Ask a question"
          className="min-w-0 flex-1 rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-slate-900"
        />

        {disabled && onStop ? (
          <button
            type="button"
            onClick={onStop}
            className="flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-3 font-semibold text-slate-900 hover:bg-slate-50"
          >
            <Square size={14} fill="currentColor" />
            Stop
          </button>
        ) : (
          <button
            type="submit"
            disabled={disabled || !question.trim()}
            className="rounded-lg bg-slate-900 px-5 py-3 font-semibold text-white disabled:opacity-60"
          >
            Send
          </button>
        )}
      </div>
    </form>
  );
}
