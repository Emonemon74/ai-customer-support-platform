"""Citations are persisted with the assistant message and survive a reload."""

import json

from tests.conftest import make_conversation

SOURCE = {"document_id": 1, "filename": "policy.pdf", "page_number": 4, "chunk_index": 2}
OTHER = {"document_id": 1, "filename": "policy.pdf", "page_number": 9, "chunk_index": 7}


def _stub_pipeline(monkeypatch, answer_tokens):
    monkeypatch.setattr(
        "app.services.chat_service.build_context",
        lambda **kwargs: ("context", [SOURCE, OTHER]),
    )
    monkeypatch.setattr(
        "app.services.chat_service.stream_answer",
        lambda **kwargs: iter(answer_tokens),
    )


def _messages(client, headers, conversation_id):
    response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages", headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_streamed_answer_persists_only_cited_sources(client, user_a, monkeypatch):
    _stub_pipeline(monkeypatch, ["Refunds take 30 days ", "[policy.pdf, page 4]."])
    conversation_id = make_conversation(client, user_a)

    response = client.post(
        "/api/v1/chat/stream",
        json={"conversation_id": conversation_id, "question": "Refund period?"},
        headers=user_a,
    )
    assert response.status_code == 200
    events = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    assert events[-1]["type"] == "done"

    user_message, assistant_message = _messages(client, user_a, conversation_id)
    assert user_message["sources"] is None
    assert assistant_message["role"] == "ASSISTANT"
    assert assistant_message["sources"] == [SOURCE]


def test_reload_matches_live_sources_event(client, user_a, monkeypatch):
    _stub_pipeline(monkeypatch, ["See [policy.pdf, page 9]."])
    conversation_id = make_conversation(client, user_a)

    response = client.post(
        "/api/v1/chat/stream",
        json={"conversation_id": conversation_id, "question": "Where?"},
        headers=user_a,
    )
    live = [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    final_sources = [e for e in live if e["type"] == "sources"][-1]["sources"]

    assistant_message = _messages(client, user_a, conversation_id)[-1]
    assert assistant_message["sources"] == final_sources == [OTHER]
