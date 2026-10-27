"""Public demo: guest sessions, usage limits and cleanup."""

from datetime import datetime, timedelta

import pytest

from app.core.settings import settings
from app.demo.service import SAMPLES_DIR, DemoService
from app.models.conversation import Conversation
from app.models.document import Document
from app.models.user import User
from tests.conftest import PDF_BYTES, make_conversation

SOURCE = {"document_id": 1, "filename": "policy.pdf", "page_number": 4, "chunk_index": 2}


@pytest.fixture
def demo_on(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_ENABLED", True)


def _start_demo(client):
    response = client.post("/api/v1/auth/demo")
    assert response.status_code == 201, response.text
    body = response.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["conversation_id"]


def _stub_chat(monkeypatch):
    monkeypatch.setattr(
        "app.services.chat_service.build_context",
        lambda **kwargs: ("context", [SOURCE]),
    )
    monkeypatch.setattr(
        "app.services.chat_service.stream_answer",
        lambda **kwargs: iter(["Answer [policy.pdf, page 4]."]),
    )


def _ask(client, headers, conversation_id):
    return client.post(
        "/api/v1/chat/stream",
        json={"conversation_id": conversation_id, "question": "Refunds?"},
        headers=headers,
    )


def _upload(client, headers, conversation_id, content):
    return client.post(
        "/api/v1/documents/upload",
        data={"conversation_id": conversation_id},
        files={"file": ("doc.pdf", content, "application/pdf")},
        headers=headers,
    )


def test_demo_is_404_when_disabled(client):
    assert client.post("/api/v1/auth/demo").status_code == 404
    assert client.get("/api/v1/config").json()["demo_enabled"] is False


def test_config_reports_demo_enabled(client, demo_on):
    assert client.get("/api/v1/config").json()["demo_enabled"] is True


def test_demo_session_comes_with_sample_documents(client, demo_on):
    headers, conversation_id = _start_demo(client)

    me = client.get("/api/v1/users/me", headers=headers).json()
    assert me["is_demo"] is True

    documents = client.get(
        f"/api/v1/documents?conversation_id={conversation_id}", headers=headers
    ).json()
    expected = {f"{path.stem}.pdf" for path in SAMPLES_DIR.glob("*.txt")}
    assert {d["filename"] for d in documents} == expected
    assert all(d["status"] == "READY" for d in documents)


def test_demo_sessions_are_isolated_from_each_other(client, demo_on):
    _, first_conversation = _start_demo(client)
    second_headers, _ = _start_demo(client)

    response = client.get(
        f"/api/v1/conversations/{first_conversation}", headers=second_headers
    )
    assert response.status_code == 404


def test_demo_user_hits_message_limit(client, demo_on, monkeypatch):
    _stub_chat(monkeypatch)
    monkeypatch.setattr(settings, "DEMO_MAX_MESSAGES", 2)
    headers, conversation_id = _start_demo(client)

    assert _ask(client, headers, conversation_id).status_code == 200
    assert _ask(client, headers, conversation_id).status_code == 200

    blocked = _ask(client, headers, conversation_id)
    assert blocked.status_code == 429
    assert "Demo limit reached" in blocked.json()["message"]


def test_regular_user_is_not_subject_to_demo_message_limit(client, user_a, monkeypatch):
    _stub_chat(monkeypatch)
    monkeypatch.setattr(settings, "DEMO_MAX_MESSAGES", 1)
    conversation_id = make_conversation(client, user_a)

    assert _ask(client, user_a, conversation_id).status_code == 200
    assert _ask(client, user_a, conversation_id).status_code == 200


def test_global_daily_limit_returns_503_for_everyone(client, user_a, monkeypatch):
    _stub_chat(monkeypatch)
    monkeypatch.setattr(settings, "GLOBAL_DAILY_CHAT_LIMIT", 1)
    conversation_id = make_conversation(client, user_a)

    assert _ask(client, user_a, conversation_id).status_code == 200

    blocked = _ask(client, user_a, conversation_id)
    assert blocked.status_code == 503
    assert "daily question budget" in blocked.json()["message"]


def test_demo_upload_size_is_capped(client, demo_on, monkeypatch):
    headers, conversation_id = _start_demo(client)
    monkeypatch.setattr(settings, "DEMO_MAX_FILE_MB", 0)

    response = _upload(client, headers, conversation_id, PDF_BYTES)

    assert response.status_code == 400


def test_document_count_is_capped_per_user(client, user_a, monkeypatch):
    monkeypatch.setattr(settings, "MAX_DOCUMENTS_PER_USER", 1)
    conversation_id = make_conversation(client, user_a)

    assert _upload(client, user_a, conversation_id, PDF_BYTES).status_code == 202

    second = _upload(client, user_a, conversation_id, PDF_BYTES + b"x")
    assert second.status_code == 429
    assert "Document limit reached" in second.json()["message"]


def test_expired_demo_users_are_purged_with_their_data(client, db, demo_on):
    _start_demo(client)
    _start_demo(client)
    old_user = db.query(User).filter(User.is_demo.is_(True)).first()
    old_user.created_at = datetime.utcnow() - timedelta(
        hours=settings.DEMO_USER_TTL_HOURS + 1
    )
    old_id = old_user.id
    db.commit()

    purged = DemoService(db).purge_expired()

    assert purged == 1
    assert db.query(User).filter(User.id == old_id).first() is None
    assert db.query(Conversation).filter(Conversation.user_id == old_id).count() == 0
    assert db.query(Document).filter(Document.uploaded_by == old_id).count() == 0
    # The fresh guest is untouched.
    assert db.query(User).filter(User.is_demo.is_(True)).count() == 1
