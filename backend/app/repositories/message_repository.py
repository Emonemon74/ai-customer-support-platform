from datetime import datetime

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message


class MessageRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        conversation_id: int,
        role: str,
        content: str,
        sources: list[dict] | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources=sources,
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return message

    def get_by_conversation(
        self,
        conversation_id: int,
    ):
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .all()
        )


    def get_recent_messages(
        self,
        conversation_id: int,
        limit: int = 10,
    ):
        return (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()
        )



    def count_questions_by_user(self, user_id: int) -> int:
        """USER messages across all of one user's conversations."""
        return (
            self.db.query(Message)
            .join(Conversation, Conversation.id == Message.conversation_id)
            .filter(Conversation.user_id == user_id, Message.role == "USER")
            .count()
        )

    def count_questions_since(self, since: datetime) -> int:
        return (
            self.db.query(Message)
            .filter(Message.role == "USER", Message.created_at >= since)
            .count()
        )

    def delete_by_conversation(
        self,
        conversation_id: int,
    ) -> None:
        self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).delete()

        self.db.commit()
