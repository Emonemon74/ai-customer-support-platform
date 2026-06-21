import { api } from "../api/client";

export type Source = {
  document_id: number;
  chunk_index: number;
};

export type ChatResponse = {
  answer: string;
  sources: Source[];
};

export type StreamEvent =
  | {
      type: "token";
      content: string;
    }
  | {
      type: "done";
    }
  | {
      type: "error";
      message: string;
    };

export async function askQuestion(
  conversationId: number,
  question: string
) {
  const response = await api.post<ChatResponse>("/api/v1/chat/ask", {
    conversation_id: conversationId,
    question,
  });

  return response.data;
}

export async function streamQuestion(
  conversationId: number,
  question: string,
  onToken: (token: string) => void
) {
  const token = localStorage.getItem("access_token");

  const response = await fetch("http://127.0.0.1:8000/api/v1/chat/stream", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      conversation_id: conversationId,
      question,
    }),
  });

  if (!response.ok) {
    throw new Error("Streaming request failed");
  }

  if (!response.body) {
    throw new Error("No response body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const event of events) {
      if (!event.startsWith("data: ")) continue;

      const rawData = event.replace("data: ", "").trim();

      if (!rawData) continue;

      const parsedEvent = JSON.parse(rawData) as StreamEvent;

      if (parsedEvent.type === "token") {
        onToken(parsedEvent.content);
      }

      if (parsedEvent.type === "error") {
        throw new Error(parsedEvent.message);
      }

      if (parsedEvent.type === "done") {
        return;
      }
    }
  }
}