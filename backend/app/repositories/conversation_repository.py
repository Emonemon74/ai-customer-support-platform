from sqlalchemy.orm import Session

from app.models.conversation import Conversation


class ConversationRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        title: str,
        user_id: int,
    ) -> Conversation:

        conversation = Conversation(
            title=title,
            user_id=user_id,
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        return conversation

    def get_by_id(
        self,
        conversation_id: int,
    ):
        return (
            self.db.query(Conversation)
            .filter(Conversation.id == conversation_id)
            .first()
        )

    def get_by_user(
        self,
        user_id: int,
    ):
        return (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
            .all()
        )

    def delete(
        self,
        conversation: Conversation,
    ):
        self.db.delete(conversation)
        self.db.commit()