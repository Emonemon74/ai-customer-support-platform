from app.ai import cache, rag


def test_identical_query_is_served_from_cache(monkeypatch):
    calls = []

    def fake_uncached(question, user_id, conversation_id):
        calls.append(question)
        return ("context text", [{"filename": "a.pdf", "page_number": 1}])

    monkeypatch.setattr(rag, "_build_context_uncached", fake_uncached)

    first = rag.build_context("What is the refund window?", user_id=1, conversation_id=7)
    second = rag.build_context("what is the REFUND window?", user_id=1, conversation_id=7)

    assert first == second
    assert len(calls) == 1  # second call hit the cache (case/space-insensitive key)


def test_document_change_invalidates_the_cache(monkeypatch):
    monkeypatch.setattr(
        rag, "_build_context_uncached",
        lambda q, u, c: ("ctx", []),
    )

    rag.build_context("q", user_id=1, conversation_id=9)
    key_before = rag._cache_key("q", 1, 9)

    cache.bump_conversation(9)
    key_after = rag._cache_key("q", 1, 9)

    assert key_before != key_after
    assert cache.get(key_after) is None
