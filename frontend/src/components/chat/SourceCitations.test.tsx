import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SourceCitations } from "./SourceCitations";

describe("SourceCitations", () => {
  it("renders nothing without sources", () => {
    const { container } = render(<SourceCitations sources={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("labels each source with filename and page", () => {
    render(
      <SourceCitations
        sources={[
          { document_id: 1, filename: "policy.pdf", page_number: 4 },
          { document_id: 2, filename: "manual.pdf", page_number: null },
        ]}
      />
    );

    expect(screen.getByText("policy.pdf · p.4")).toBeInTheDocument();
    expect(screen.getByText("manual.pdf")).toBeInTheDocument();
  });

  it("collapses chunks from the same page into one chip", () => {
    render(
      <SourceCitations
        sources={[
          { document_id: 1, filename: "policy.pdf", page_number: 4, chunk_index: 1 },
          { document_id: 1, filename: "policy.pdf", page_number: 4, chunk_index: 2 },
          { document_id: 1, filename: "policy.pdf", page_number: 9, chunk_index: 5 },
        ]}
      />
    );

    expect(screen.getAllByText("policy.pdf · p.4")).toHaveLength(1);
    expect(screen.getByText("policy.pdf · p.9")).toBeInTheDocument();
  });
});
