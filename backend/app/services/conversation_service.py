from sqlalchemy.orm import Session

from app.ai.llm import generate_conversation_title
from app.core.exceptions.conversation import (
    ConversationAccessDeniedError,
    ConversationDeleteDeniedError,
    ConversationNotFoundError,
    ConversationRenameDeniedError,
)
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.conversation import ConversationCreateRequest
from app.services.document_service import DocumentService


class ConversationService:

    def __init__(self, db: Session):
        self.conversation_repository = ConversationRepository(db)
        self.document_repository = DocumentRepository(db)
        self.document_service = DocumentService(db)
        self.message_repository = MessageRepository(db)

    def create_conversation(
        self,
        request: ConversationCreateRequest,
        current_user: User,
    ):
        title = generate_conversation_title(request.question)

        return self.conversation_repository.create(
            title=title,
            user_id=current_user.id,
        )

    def list_conversations(self, current_user: User):
        return self.conversation_repository.get_by_user(current_user.id)

    def get_messages(
        self,
        conversation_id: int,
        current_user: User,
    ):
        conversation = self.conversation_repository.get_by_id(conversation_id)

        if not conversation:
            raise ConversationNotFoundError()

        if conversation.user_id != current_user.id:
            raise ConversationAccessDeniedError()

        return self.message_repository.get_by_conversation(conversation_id)

    def rename_conversation(
        self,
        conversation_id: int,
        title: str,
        current_user: User,
    ):
        conversation = self.conversation_repository.get_by_id(conversation_id)

        if not conversation:
            raise ConversationNotFoundError()

        if conversation.user_id != current_user.id:
            raise ConversationRenameDeniedError()

        return self.conversation_repository.update_title(
            conversation=conversation,
            title=title,
        )

    def delete_conversation(
        self,
        conversation_id: int,
        current_user: User,
    ):
        conversation = self.conversation_repository.get_by_id(conversation_id)

        if not conversation:
            raise ConversationNotFoundError()

        if conversation.user_id != current_user.id:
            raise ConversationDeleteDeniedError()

        documents = self.document_repository.get_all_by_conversation(conversation_id)

        for document in documents:
            self.document_service.delete_document_record(document)

        self.message_repository.delete_by_conversation(conversation_id)
        self.conversation_repository.delete(conversation)

        return {
            "message": "Conversation deleted successfully"
        }

    def search_conversations(
        self,
        query: str,
        current_user: User,
    ):
        return self.conversation_repository.search_by_title(
            user_id=current_user.id,
            query=query,
        )
