from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.conversation import ConversationCreateRequest
from app.ai.llm import generate_conversation_title


class ConversationService:

    def __init__(self, db: Session):
        self.conversation_repository = ConversationRepository(db)
        self.message_repository = MessageRepository(db)

    def create_conversation(
        self,
        request: ConversationCreateRequest,
        current_user: User,
    ):
        title = generate_conversation_title(
            request.question
        )

        return self.conversation_repository.create(
            title=title,
            user_id=current_user.id,
        )

    def list_conversations(self, current_user: User):
        return self.conversation_repository.get_by_user(current_user.id)

    def get_messages(self, conversation_id: int, current_user: User):
        conversation = self.conversation_repository.get_by_id(conversation_id)

        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.user_id != current_user.id:
            raise ValueError("You are not authorized to access this conversation")

        return self.message_repository.get_by_conversation(conversation_id)
    

    def rename_conversation(
        self,
        conversation_id: int,
        title: str,
        current_user: User,
    ):
        conversation = self.conversation_repository.get_by_id(conversation_id)

        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.user_id != current_user.id:
            raise ValueError("You are not authorized to rename this conversation")

        return self.conversation_repository.update_title(
            conversation=conversation,
            title=title,
        )