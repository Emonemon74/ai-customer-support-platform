import { useEffect, useRef, useState } from "react";
import toast from "react-hot-toast";

import { Bot, Check, Copy, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";

import { ChatInput } from "./ChatInput";
import { SourceCitations } from "./SourceCitations";

import type { Source } from "../../services/chat.service";
import type { Message } from "../../services/message.service";

type ChatWindowProps = {
  title?: string;
  messages: Message[];
  disabled?: boolean;
  onSend: (question: string) => Promise<void>;
  sources: Source[];
};

export function ChatWindow({
  title,
  messages,
  disabled,
  onSend,
  sources,
}: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  const [copiedMessageId, setCopiedMessageId] = useState<string | number | null>(
    null
  );

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  async function handleCopyMessage(messageId: string | number, content: string) {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      toast.success("Message copied");

      setTimeout(() => {
        setCopiedMessageId(null);
      }, 1500);
    } catch (error) {
      console.error("Failed to copy message:", error);
      toast.error("Failed to copy message");
    }
  }

  async function handleCopyCode(code: string) {
    try {
      await navigator.clipboard.writeText(code);
      toast.success("Code copied");
    } catch (error) {
      console.error("Failed to copy code:", error);
      toast.error("Failed to copy code");
    }
  }

  return (
    <main className="flex min-h-0 flex-1 flex-col bg-slate-50">
      <div className="border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
        <h2 className="truncate text-lg font-bold text-slate-900">
          {title || "Select a conversation"}
        </h2>
      </div>

      <div className="min-h-0 flex-1 space-y-6 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-center">
            <div className="rounded-2xl bg-white px-10 py-8 shadow-sm">
              <h3 className="text-2xl font-bold text-slate-900">
                Welcome to your AI workspace
              </h3>

              <p className="mt-2 text-sm text-slate-600">
                Select a conversation to view messages.
              </p>
            </div>
          </div>
        ) : (
          messages.map((message) => {
            const isUser = message.role === "USER";

            return (
              <div
                key={message.id}
                className={`group flex items-start gap-3 ${
                  isUser ? "justify-end" : "justify-start"
                }`}
              >
                {!isUser && (
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-900 text-white shadow-sm">
                    <Bot size={20} />
                  </div>
                )}

                {isUser && (
                  <button
                    type="button"
                    onClick={() =>
                      handleCopyMessage(message.id, message.content)
                    }
                    title="Copy message"
                    className="mt-3 rounded-lg p-1.5 text-slate-400 opacity-0 transition hover:bg-white hover:text-slate-700 hover:shadow-sm group-hover:opacity-100"
                  >
                    {copiedMessageId === message.id ? (
                      <Check size={16} />
                    ) : (
                      <Copy size={16} />
                    )}
                  </button>
                )}

                <div
                  className={`max-w-[75%] rounded-2xl px-5 py-4 text-sm leading-7 shadow-sm transition ${
                    isUser
                      ? "rounded-tr-md bg-slate-900 text-white"
                      : "rounded-tl-md border border-slate-200 bg-white text-slate-800"
                  }`}
                >
                  <div className="mb-2 text-xs font-semibold opacity-60">
                    {isUser ? "You" : "AI Assistant"}
                  </div>

                  <div
                    className={`prose prose-sm max-w-none leading-7
                      prose-headings:mb-3 prose-headings:mt-4 prose-headings:font-bold prose-headings:text-slate-900
                      prose-h1:text-xl prose-h2:text-lg prose-h3:text-base
                      prose-p:my-3 prose-p:leading-7
                      prose-ul:my-3 prose-ul:list-disc prose-ul:pl-6
                      prose-ol:my-3 prose-ol:list-decimal prose-ol:pl-6
                      prose-li:my-1
                      prose-blockquote:my-4 prose-blockquote:rounded-r-lg prose-blockquote:border-l-4 prose-blockquote:border-slate-300 prose-blockquote:bg-slate-50 prose-blockquote:px-4 prose-blockquote:py-2 prose-blockquote:text-slate-600 prose-blockquote:not-italic
                      prose-table:my-4 prose-table:w-full prose-table:border-collapse
                      prose-th:border prose-th:border-slate-300 prose-th:bg-slate-100 prose-th:px-3 prose-th:py-2 prose-th:text-left
                      prose-td:border prose-td:border-slate-200 prose-td:px-3 prose-td:py-2
                      prose-a:font-medium prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
                      prose-strong:text-slate-900
                      prose-code:rounded prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:text-sm prose-code:font-medium prose-code:text-pink-700
                      prose-pre:m-0 prose-pre:p-0
                      prose-code:before:content-none prose-code:after:content-none
                      ${
                        isUser
                          ? "prose-invert prose-headings:text-white prose-strong:text-white prose-code:bg-slate-800 prose-code:text-slate-100"
                          : "prose-slate"
                      }`}
                  >
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        code(props) {
                          const { children, className } = props;
                          const match = /language-(\w+)/.exec(
                            className || ""
                          );
                          const codeText = String(children).replace(/\n$/, "");

                          if (match) {
                            return (
                              <div className="group/code relative my-4 overflow-hidden rounded-xl border border-slate-700 bg-slate-950 shadow-sm">
                                <div className="flex items-center justify-between border-b border-slate-700 bg-slate-900 px-4 py-2">
                                  <span className="text-xs font-medium uppercase tracking-wide text-slate-400">
                                    {match[1]}
                                  </span>

                                  <button
                                    type="button"
                                    onClick={() => handleCopyCode(codeText)}
                                    className="rounded-md px-2 py-1 text-xs font-medium text-slate-300 transition hover:bg-slate-800 hover:text-white"
                                  >
                                    Copy
                                  </button>
                                </div>

                                <SyntaxHighlighter
                                  style={oneDark}
                                  language={match[1]}
                                  PreTag="div"
                                  customStyle={{
                                    margin: 0,
                                    borderRadius: 0,
                                    background: "transparent",
                                    padding: "16px",
                                  }}
                                >
                                  {codeText}
                                </SyntaxHighlighter>
                              </div>
                            );
                          }

                          return (
                            <code className={className}>{children}</code>
                          );
                        },
                      }}
                    >
                      {message.content}
                    </ReactMarkdown>
                  </div>
                </div>

                {!isUser && (
                  <button
                    type="button"
                    onClick={() =>
                      handleCopyMessage(message.id, message.content)
                    }
                    title="Copy message"
                    className="mt-3 rounded-lg p-1.5 text-slate-400 opacity-0 transition hover:bg-white hover:text-slate-700 hover:shadow-sm group-hover:opacity-100"
                  >
                    {copiedMessageId === message.id ? (
                      <Check size={16} />
                    ) : (
                      <Copy size={16} />
                    )}
                  </button>
                )}

                {isUser && (
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-300 text-slate-800 shadow-sm">
                    <User size={20} />
                  </div>
                )}
              </div>
            );
          })
        )}

        {disabled && (
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-900 text-white shadow-sm">
              <Bot size={20} />
            </div>

            <div className="rounded-2xl rounded-tl-md border border-slate-200 bg-white px-5 py-4 text-sm text-slate-500 shadow-sm">
              AI is thinking...
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <SourceCitations sources={sources} />

      <ChatInput disabled={disabled} onSend={onSend} />
    </main>
  );
}