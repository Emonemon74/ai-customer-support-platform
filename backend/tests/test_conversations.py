from tests.conftest import make_conversation


def test_create_and_list_conversation(client, user_a):
    conversation_id = make_conversation(client, user_a)

    listing = client.get("/api/v1/conversations", headers=user_a)
    assert listing.status_code == 200
    assert [c["id"] for c in listing.json()] == [conversation_id]


def test_rename_conversation(client, user_a):
    conversation_id = make_conversation(client, user_a)
    response = client.patch(
        f"/api/v1/conversations/{conversation_id}",
        json={"title": "Renamed"},
        headers=user_a,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Renamed"


def test_delete_conversation_removes_it(client, user_a):
    conversation_id = make_conversation(client, user_a)
    assert (
        client.delete(
            f"/api/v1/conversations/{conversation_id}", headers=user_a
        ).status_code
        == 200
    )
    assert client.get("/api/v1/conversations", headers=user_a).json() == []


def test_missing_conversation_returns_404(client, user_a):
    assert (
        client.get(
            "/api/v1/conversations/999999/messages", headers=user_a
        ).status_code
        == 404
    )
