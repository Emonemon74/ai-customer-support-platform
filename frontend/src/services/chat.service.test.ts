import { afterEach, describe, expect, it, vi } from "vitest";

import { streamQuestion, type Source } from "./chat.service";

const encoder = new TextEncoder();

function sse(...events: object[]) {
  return events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join("");
}

// Deliver the body in the given chunks, as the network might split it.
function mockStream(chunks: string[], init: { ok?: boolean } = {}) {
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(encoder.encode(chunk));
      controller.close();
    },
  });

  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: init.ok ?? true, body })
  );
}

const SOURCE: Source = {
  document_id: 1,
  filename: "policy.pdf",
  page_number: 4,
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("streamQuestion", () => {
  it("emits tokens and sources in order and stops at done", async () => {
    mockStream([
      sse(
        { type: "sources", sources: [SOURCE] },
        { type: "token", content: "Hello " },
        { type: "token", content: "world" },
        { type: "sources", sources: [SOURCE] },
        { type: "done" }
      ),
    ]);

    const tokens: string[] = [];
    const sources: Source[][] = [];

    await streamQuestion(1, "hi", (t) => tokens.push(t), (s) => sources.push(s));

    expect(tokens).toEqual(["Hello ", "world"]);
    expect(sources).toEqual([[SOURCE], [SOURCE]]);
  });

  it("reassembles an event split across network chunks", async () => {
    const payload = sse({ type: "token", content: "split" }, { type: "done" });
    mockStream([payload.slice(0, 10), payload.slice(10, 25), payload.slice(25)]);

    const tokens: string[] = [];
    await streamQuestion(1, "hi", (t) => tokens.push(t));

    expect(tokens).toEqual(["split"]);
  });

  it("sends the bearer token and conversation id", async () => {
    localStorage.setItem("access_token", "abc123");
    mockStream([sse({ type: "done" })]);

    await streamQuestion(7, "why?", () => {});

    const [, init] = vi.mocked(fetch).mock.calls[0];
    expect(init?.headers).toMatchObject({ Authorization: "Bearer abc123" });
    expect(JSON.parse(init?.body as string)).toEqual({
      conversation_id: 7,
      question: "why?",
    });
  });

  it("throws the server message on an error event", async () => {
    mockStream([sse({ type: "error", message: "Something went wrong" })]);

    await expect(streamQuestion(1, "hi", () => {})).rejects.toThrow(
      "Something went wrong"
    );
  });

  it("throws when the request is rejected", async () => {
    mockStream([], { ok: false });

    await expect(streamQuestion(1, "hi", () => {})).rejects.toThrow(
      "Streaming request failed"
    );
  });
});

describe("streamQuestion cancellation", () => {
  it("passes the abort signal to fetch and rejects when aborted", async () => {
    const controller = new AbortController();
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: string, init: RequestInit) =>
        new Promise((_resolve, reject) => {
          init.signal?.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError"))
          );
        })
      )
    );

    const pending = streamQuestion(1, "hi", () => {}, undefined, controller.signal);
    controller.abort();

    await expect(pending).rejects.toMatchObject({ name: "AbortError" });
    expect(vi.mocked(fetch).mock.calls[0][1]?.signal).toBe(controller.signal);
  });
});
