"""When the conversation's documents return candidates, the model gets context
even if the cross-encoder scored them below the relevance threshold -- the
grounding prompt is the real guardrail against answering off-topic questions."""

from app.ai import rag

_LOW_SCORE_HITS = [
    {"text": "Acme Cloud billing policy. Plans: Starter, Team, Enterprise.",
     "metadata": {"filename": "billing.pdf", "page_number": 1, "document_id": 1,
                  "conversation_id": 5, "chunk_index": 0},
     "rerank_score": 0.001},
    {"text": "Refunds within 30 days of first payment.",
     "metadata": {"filename": "billing.pdf", "page_number": 2, "document_id": 1,
                  "conversation_id": 5, "chunk_index": 1},
     "rerank_score": 0.0},
]


def test_low_scoring_candidates_are_still_passed_as_context(monkeypatch):
    monkeypatch.setattr(rag, "hybrid_search", lambda **kw: _LOW_SCORE_HITS)

    context, sources = rag._build_context_uncached("Summarize this document", 1, 5)

    assert context  # not empty -> the model can actually answer
    assert sources[0]["filename"] == "billing.pdf"


def test_empty_retrieval_still_hands_over_no_context(monkeypatch):
    monkeypatch.setattr(rag, "hybrid_search", lambda **kw: [])

    context, sources = rag._build_context_uncached("anything", 1, 5)

    assert context == ""
    assert sources == []


def test_relevant_hits_are_preferred_when_some_clear_the_bar(monkeypatch):
    hits = [
        {"text": "high", "metadata": {"filename": "a.pdf", "page_number": 1,
                                      "document_id": 1, "conversation_id": 5,
                                      "chunk_index": 0}, "rerank_score": 0.9},
        {"text": "low", "metadata": {"filename": "a.pdf", "page_number": 2,
                                     "document_id": 1, "conversation_id": 5,
                                     "chunk_index": 1}, "rerank_score": 0.01},
    ]
    monkeypatch.setattr(rag, "hybrid_search", lambda **kw: hits)

    context, _ = rag._build_context_uncached("q", 1, 5)

    assert "high" in context
    assert "low" not in context
