import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { Message } from "../../services/message.service";
import { ChatWindow } from "./ChatWindow";

function message(overrides: Partial<Message>): Message {
  return {
    id: 1,
    conversation_id: 1,
    role: "ASSISTANT",
    content: "",
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("ChatWindow citations", () => {
  it("shows each answer's own sources under that answer", () => {
    render(
      <ChatWindow
        messages={[
          message({ id: 1, role: "USER", content: "Refunds?" }),
          message({
            id: 2,
            content: "30 days [policy.pdf, page 4]",
            sources: [{ document_id: 1, filename: "policy.pdf", page_number: 4 }],
          }),
          message({ id: 3, role: "USER", content: "Shipping?" }),
          message({
            id: 4,
            content: "Ships in 2 days [shipping.pdf, page 1]",
            sources: [{ document_id: 2, filename: "shipping.pdf", page_number: 1 }],
          }),
        ]}
        onSend={vi.fn()}
      />
    );

    // Both stay visible: a later answer no longer replaces earlier citations.
    expect(screen.getByText("policy.pdf · p.4")).toBeInTheDocument();
    expect(screen.getByText("shipping.pdf · p.1")).toBeInTheDocument();
  });

  it("shows no sources for an abstention or a user message", () => {
    render(
      <ChatWindow
        messages={[
          message({ id: 1, role: "USER", content: "Weather?" }),
          message({ id: 2, content: "Not found in the documents.", sources: [] }),
        ]}
        onSend={vi.fn()}
      />
    );

    expect(screen.queryByText(/grounded in your documents/)).not.toBeInTheDocument();
  });
});
