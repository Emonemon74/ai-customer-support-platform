from tests.conftest import PDF_BYTES, make_conversation


def _upload(client, headers, conversation_id, content=PDF_BYTES, filename="policy.pdf",
            content_type="application/pdf"):
    return client.post(
        "/api/v1/documents/upload",
        data={"conversation_id": conversation_id},
        files={"file": (filename, content, content_type)},
        headers=headers,
    )


def test_upload_then_list_and_get(client, user_a):
    conversation_id = make_conversation(client, user_a)
    document_id = _upload(client, user_a, conversation_id).json()["id"]

    listing = client.get(
        f"/api/v1/documents?conversation_id={conversation_id}", headers=user_a
    )
    assert [d["id"] for d in listing.json()] == [document_id]

    fetched = client.get(
        f"/api/v1/documents/{document_id}?conversation_id={conversation_id}",
        headers=user_a,
    )
    assert fetched.status_code == 200
    assert fetched.json()["filename"] == "policy.pdf"


def test_upload_rejects_unsupported_type(client, user_a):
    conversation_id = make_conversation(client, user_a)
    response = _upload(
        client, user_a, conversation_id,
        content=b"plain text", filename="notes.txt", content_type="text/plain",
    )
    assert response.status_code == 400


def test_upload_rejects_empty_file(client, user_a):
    conversation_id = make_conversation(client, user_a)
    response = _upload(client, user_a, conversation_id, content=b"")
    assert response.status_code == 400


def test_delete_document(client, user_a):
    conversation_id = make_conversation(client, user_a)
    document_id = _upload(client, user_a, conversation_id).json()["id"]

    assert (
        client.delete(
            f"/api/v1/documents/{document_id}?conversation_id={conversation_id}",
            headers=user_a,
        ).status_code
        == 200
    )
    assert client.get(
        f"/api/v1/documents?conversation_id={conversation_id}", headers=user_a
    ).json() == []
