"""Live retrieval tests against a real (ephemeral) Chroma collection.

These exercise the isolation filter and the hybrid pipeline end to end. They
use the bundled ONNX embedding model, which is cached after the first run.
"""

import uuid

import pytest

pytestmark = pytest.mark.usefixtures("_fresh_database")


@pytest.fixture
def store(monkeypatch):
    import chromadb

    from app.ai import hybrid_retriever, vector_store

    # EphemeralClient instances share process-global storage, so each test
    # needs its own uniquely named collection.
    client = chromadb.EphemeralClient()
    collection = client.get_or_create_collection(name=f"test-{uuid.uuid4().hex}")

    monkeypatch.setattr(vector_store, "collection", collection)
    monkeypatch.setattr(hybrid_retriever, "collection", collection)

    return vector_store.VectorStore()


def _add(store, document_id, user_id, conversation_id, texts):
    chunks = [
        {"text": t, "page_number": i + 1, "chunk_index": i}
        for i, t in enumerate(texts)
    ]
    store.add_document(
        document_id=document_id,
        chunks=chunks,
        user_id=user_id,
        conversation_id=conversation_id,
        filename=f"doc{document_id}.pdf",
    )


def test_retrieval_is_scoped_to_user_and_conversation(store):
    from app.ai.hybrid_retriever import hybrid_search

    _add(store, 1, user_id=1, conversation_id=10, texts=[
        "The refund window is 30 days from first payment.",
        "Annual plans receive a 20 percent discount.",
    ])
    _add(store, 2, user_id=2, conversation_id=20, texts=[
        "The refund window is 90 days for enterprise customers.",
    ])

    results = hybrid_search("how long is the refund window", user_id=1, conversation_id=10, mode="hybrid")

    assert results
    for r in results:
        assert r["metadata"]["user_id"] == 1
        assert r["metadata"]["conversation_id"] == 10
    assert not any("90 days" in r["text"] for r in results)


def test_hybrid_finds_keyword_only_match(store):
    from app.ai.hybrid_retriever import hybrid_search

    _add(store, 1, user_id=1, conversation_id=10, texts=[
        "Press G then S to jump to Settings.",
        "Invites expire after 14 days.",
        "The maximum imported file size is 20 MB.",
    ])

    results = hybrid_search("SIEM webhook export", user_id=1, conversation_id=10, mode="hybrid", top_n=3)
    # nothing matches -> BM25 contributes nothing, dense returns best-effort
    assert isinstance(results, list)

    results = hybrid_search("14 days", user_id=1, conversation_id=10, mode="hybrid", top_n=3)
    assert any("14 days" in r["text"] for r in results)


def test_missing_scope_is_rejected(store):
    from app.ai.hybrid_retriever import hybrid_search

    with pytest.raises(ValueError):
        hybrid_search("anything", user_id=0, conversation_id=10)
