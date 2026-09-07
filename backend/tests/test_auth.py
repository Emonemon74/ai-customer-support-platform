def test_signup_returns_token(client):
    response = client.post(
        "/api/v1/auth",
        json={"full_name": "New Person", "email": "new@example.com", "password": "pw-12345"},
    )
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_with_wrong_password_is_rejected(client):
    client.post(
        "/api/v1/auth",
        json={"full_name": "Person", "email": "p@example.com", "password": "right-pw"},
    )
    response = client.post(
        "/api/v1/auth",
        json={"email": "p@example.com", "password": "wrong-pw"},
    )
    assert response.status_code == 401


def test_signup_without_full_name_is_rejected(client):
    response = client.post(
        "/api/v1/auth",
        json={"email": "nameless@example.com", "password": "pw-12345"},
    )
    assert response.status_code == 401


def test_me_requires_authentication(client):
    assert client.get("/api/v1/users/me").status_code == 401  # no bearer header


def test_me_rejects_garbage_token(client):
    response = client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401


def test_me_returns_current_user(client, user_a):
    response = client.get("/api/v1/users/me", headers=user_a)
    assert response.status_code == 200
    assert response.json()["email"] == "user_a@example.com"
