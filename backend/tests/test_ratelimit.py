from app.core import ratelimit
from tests.conftest import make_conversation


def test_auth_endpoint_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(ratelimit.settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(ratelimit, "_store", ratelimit._FixedWindow())

    payload = {"email": "spam@example.com", "password": "wrong-password"}

    statuses = [
        client.post("/api/v1/auth/login", json=payload).status_code for _ in range(12)
    ]

    assert 429 in statuses
    # The default budget is 10/minute, so the 11th call is the first to trip.
    assert statuses.index(429) == 10


def test_security_headers_present(client):
    headers = client.get("/health").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"


def test_chat_has_a_daily_budget_per_ip_for_every_user(client, user_a, monkeypatch):
    monkeypatch.setattr(ratelimit.settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(ratelimit, "_store", ratelimit._FixedWindow())
    monkeypatch.setattr(
        "app.services.chat_service.build_context", lambda **kwargs: ("context", [])
    )
    monkeypatch.setattr(
        "app.services.chat_service.stream_answer", lambda **kwargs: iter(["ok"])
    )
    from app.api.v1 import chat

    monkeypatch.setattr(chat._chat_daily_limit, "limit", 2)
    conversation_id = make_conversation(client, user_a)

    def ask():
        return client.post(
            "/api/v1/chat/stream",
            json={"conversation_id": conversation_id, "question": "Refunds?"},
            headers=user_a,
        ).status_code

    assert [ask(), ask(), ask()] == [200, 200, 429]


def test_rate_limit_table_drops_expired_windows(monkeypatch):
    monkeypatch.setattr(ratelimit, "_PRUNE_THRESHOLD", 3)
    store = ratelimit._FixedWindow()
    for i in range(4):
        store.check(f"k{i}", limit=1, window=0.0)

    store.check("fresh", limit=1, window=60.0)

    assert set(store._hits) == {"fresh"}


def test_chat_question_length_is_capped(client, user_a):
    conversation_id = make_conversation(client, user_a)

    response = client.post(
        "/api/v1/chat/stream",
        json={"conversation_id": conversation_id, "question": "x" * 2001},
        headers=user_a,
    )

    assert response.status_code == 422
