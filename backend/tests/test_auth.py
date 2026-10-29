REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"


def _register(client, email="p@example.com", password="right-pw-1"):
    return client.post(
        REGISTER,
        json={"full_name": "Person", "email": email, "password": password},
    )


def test_register_returns_token(client):
    response = _register(client)
    assert response.status_code == 201
    assert response.json()["access_token"]


def test_register_duplicate_email_conflicts(client):
    _register(client)
    assert _register(client).status_code == 409


def test_register_requires_full_name_and_valid_fields(client):
    for payload in (
        {"email": "a@example.com", "password": "pw-12345"},
        {"full_name": "A", "email": "not-an-email", "password": "pw-12345"},
        {"full_name": "A", "email": "a@example.com", "password": "short"},
    ):
        assert client.post(REGISTER, json=payload).status_code == 422


def test_login_returns_token(client):
    _register(client)
    response = client.post(LOGIN, json={"email": "p@example.com", "password": "right-pw-1"})
    assert response.status_code == 200
    assert response.json()["access_token"]


def test_login_wrong_password_and_unknown_email_look_identical(client):
    _register(client)
    wrong = client.post(LOGIN, json={"email": "p@example.com", "password": "wrong-pw-1"})
    unknown = client.post(LOGIN, json={"email": "nobody@example.com", "password": "wrong-pw-1"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["message"] == unknown.json()["message"]


def test_login_does_not_create_accounts(client):
    client.post(LOGIN, json={"email": "ghost@example.com", "password": "pw-12345"})
    assert client.post(LOGIN, json={"email": "ghost@example.com", "password": "pw-12345"}).status_code == 401


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
