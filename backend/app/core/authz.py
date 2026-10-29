"""Centralized resource-ownership checks.

Every authorization decision funnels through this module so the rules live in
one place. On any failure we raise ``404`` with a generic "not found" message,
never ``403`` -- a ``403`` on someone else's resource confirms that the id
exists, which is an information leak. From an attacker's point of view a
resource they do not own is indistinguishable from one that was never created.
"""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.document import Document
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository


def _not_found(resource: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} not found",
    )


def require_owned_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
) -> Conversation:
    """Return the conversation only if it exists and belongs to ``user_id``."""
    conversation = ConversationRepository(db).get_by_id(conversation_id)

    if conversation is None or conversation.user_id != user_id:
        raise _not_found("Conversation")

    return conversation


def require_owned_document(
    db: Session,
    document_id: int,
    user_id: int,
    conversation_id: int | None = None,
) -> Document:
    """Return the document only if it exists, belongs to ``user_id`` and (when
    given) is attached to ``conversation_id``."""
    document = DocumentRepository(db).get_by_id(document_id)

    if document is None or document.uploaded_by != user_id:
        raise _not_found("Document")

    if conversation_id is not None and document.conversation_id != conversation_id:
        raise _not_found("Document")

    # The document's conversation must still belong to the user.
    require_owned_conversation(db, document.conversation_id, user_id)

    return document
