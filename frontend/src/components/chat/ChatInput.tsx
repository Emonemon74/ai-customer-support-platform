import { useState } from "react";

type ChatInputProps = {
  disabled?: boolean;
  onSend: (question: string) => Promise<void>;
};

export function ChatInput({ disabled, onSend }: ChatInputProps) {
  const [question, setQuestion] = useState("");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!question.trim()) return;

    await onSend(question);
    setQuestion("");
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-slate-200 bg-white p-4"
    >
      <div className="flex gap-3">
        <input
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          disabled={disabled}
          placeholder="Ask a question..."
          className="flex-1 rounded-lg border border-slate-300 px-4 py-3 outline-none focus:border-slate-900"
        />

        <button
          type="submit"
          disabled={disabled}
          className="rounded-lg bg-slate-900 px-5 py-3 font-semibold text-white disabled:opacity-60"
        >
          Send
        </button>
      </div>
    </form>
  );
}