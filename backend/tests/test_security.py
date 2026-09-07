"""Cross-tenant isolation tests.

Each case asserts both the HTTP status *and* that the victim's data is
untouched / absent from the attacker's view.
"""

from tests.conftest import PDF_BYTES, make_conversation


def _upload(client, headers, conversation_id, filename="policy.pdf"):
    return client.post(
        "/api/v1/documents/upload",
        data={"conversation_id": conversation_id},
        files={"file": (filename, PDF_BYTES, "application/pdf")},
        headers=headers,
    )


def test_user_can_upload_to_own_conversation(client, user_a):
    conversation_id = make_conversation(client, user_a)
    response = _upload(client, user_a, conversation_id)
    assert response.status_code == 200
    assert response.json()["status"] == "READY"


def test_cannot_read_another_users_conversation_messages(client, user_a, user_b):
    conversation_id = make_conversation(client, user_a)
    response = client.get(
        f"/api/v1/conversations/{conversation_id}/messages", headers=user_b
    )
    assert response.status_code == 404


def test_cannot_rename_another_users_conversation(client, user_a, user_b):
    conversation_id = make_conversation(client, user_a)
    response = client.patch(
        f"/api/v1/conversations/{conversation_id}",
        json={"title": "hijacked"},
        headers=user_b,
    )
    assert response.status_code == 404

    # Owner still sees the original title.
    listing = client.get("/api/v1/conversations", headers=user_a).json()
    assert listing[0]["title"] == "Refund policy questions"


def test_cannot_delete_another_users_conversation(client, user_a, user_b):
    conversation_id = make_conversation(client, user_a)
    assert (
        client.delete(f"/api/v1/conversations/{conversation_id}", headers=user_b).status_code
        == 404
    )
    assert len(client.get("/api/v1/conversations", headers=user_a).json()) == 1


def test_cannot_upload_to_another_users_conversation(client, user_a, user_b):
    conversation_id = make_conversation(client, user_a)
    response = _upload(client, user_b, conversation_id)
    assert response.status_code == 404


def test_cannot_read_another_users_document(client, user_a, user_b):
    conv_a = make_conversation(client, user_a)
    document_id = _upload(client, user_a, conv_a).json()["id"]

    conv_b = make_conversation(client, user_b)
    response = client.get(
        f"/api/v1/documents/{document_id}?conversation_id={conv_b}", headers=user_b
    )
    assert response.status_code == 404


def test_cannot_delete_another_users_document(client, user_a, user_b):
    conv_a = make_conversation(client, user_a)
    document_id = _upload(client, user_a, conv_a).json()["id"]

    conv_b = make_conversation(client, user_b)
    response = client.delete(
        f"/api/v1/documents/{document_id}?conversation_id={conv_b}", headers=user_b
    )
    assert response.status_code == 404

    # The document is still there for its owner.
    still_there = client.get(
        f"/api/v1/documents/{document_id}?conversation_id={conv_a}", headers=user_a
    )
    assert still_there.status_code == 200


def test_document_listing_is_scoped_to_owner(client, user_a, user_b):
    conv_a = make_conversation(client, user_a)
    _upload(client, user_a, conv_a)

    conv_b = make_conversation(client, user_b)
    listing = client.get(
        f"/api/v1/documents?conversation_id={conv_b}", headers=user_b
    )
    assert listing.status_code == 200
    assert listing.json() == []


def test_upload_rejects_type_mismatch(client, user_a):
    conversation_id = make_conversation(client, user_a)
    response = client.post(
        "/api/v1/documents/upload",
        data={"conversation_id": conversation_id},
        files={"file": ("payload.pdf", b"MZ not really a pdf", "application/pdf")},
        headers=user_a,
    )
    assert response.status_code == 400
