from app.core import ratelimit


def test_auth_endpoint_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(ratelimit.settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(ratelimit, "_store", ratelimit._FixedWindow())

    payload = {"email": "spam@example.com", "password": "wrong-password"}

    statuses = [
        client.post("/api/v1/auth", json=payload).status_code for _ in range(12)
    ]

    assert 429 in statuses
    # The default budget is 10/minute, so the 11th call is the first to trip.
    assert statuses.index(429) == 10


def test_security_headers_present(client):
    headers = client.get("/health").headers
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
