"""Summary/overview questions must still get context even when the cross-encoder
scores every passage below the relevance threshold."""

import pytest

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


@pytest.mark.parametrize(
    "question",
    ["Summarize this document", "What are the key points?",
     "give me an overview", "what does this pdf say"],
)
def test_summary_intent_is_recognised(question):
    assert rag._looks_like_summary_request(question)


@pytest.mark.parametrize(
    "question",
    ["How many days for a refund?", "Who is the president of France?"],
)
def test_specific_questions_are_not_summary_intent(question):
    assert not rag._looks_like_summary_request(question)


def test_summary_query_gets_context_despite_low_scores(monkeypatch):
    monkeypatch.setattr(rag, "hybrid_search", lambda **kw: _LOW_SCORE_HITS)

    context, sources = rag._build_context_uncached("Summarize this document", 1, 5)

    assert context  # not empty -> the model can actually answer
    assert sources[0]["filename"] == "billing.pdf"


def test_specific_query_still_abstains_on_low_scores(monkeypatch):
    monkeypatch.setattr(rag, "hybrid_search", lambda **kw: _LOW_SCORE_HITS)

    context, sources = rag._build_context_uncached(
        "Who is the president of France?", 1, 5
    )

    assert context == ""
    assert sources == []
