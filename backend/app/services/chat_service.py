import json
from typing import Generator

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.rag import ask_question, stream_question
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.conversation_repository = ConversationRepository(db)
        self.message_repository = MessageRepository(db)

    def validate_conversation_access(
        self,
        conversation_id: int,
        current_user: User,
    ):
        conversation = self.conversation_repository.get_by_id(conversation_id)

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this conversation",
            )

        return conversation

    def build_conversation_history(self, conversation_id: int) -> str:
        history = self.message_repository.get_recent_messages(conversation_id)

        return "\n".join(
            [
                f"{message.role}: {message.content}"
                for message in reversed(history)
            ]
        )

    def ask(
        self,
        conversation_id: int,
        question: str,
        current_user: User,
    ):
        self.validate_conversation_access(
            conversation_id=conversation_id,
            current_user=current_user,
        )

        self.message_repository.create(
            conversation_id=conversation_id,
            role="USER",
            content=question,
        )

        conversation_history = self.build_conversation_history(conversation_id)

        result = ask_question(
            question=question,
            user_id=current_user.id,
            conversation_history=conversation_history,
        )

        self.message_repository.create(
            conversation_id=conversation_id,
            role="ASSISTANT",
            content=result["answer"],
        )

        return result

    def stream(
        self,
        conversation_id: int,
        question: str,
        current_user: User,
    ) -> Generator[str, None, None]:
        self.validate_conversation_access(
            conversation_id=conversation_id,
            current_user=current_user,
        )

        self.message_repository.create(
            conversation_id=conversation_id,
            role="USER",
            content=question,
        )

        conversation_history = self.build_conversation_history(conversation_id)

        full_answer = ""

        try:
            for token in stream_question(
                question=question,
                user_id=current_user.id,
                conversation_history=conversation_history,
            ):
                full_answer += token

                payload = json.dumps(
                    {
                        "type": "token",
                        "content": token,
                    }
                )

                yield f"data: {payload}\n\n"

            self.message_repository.create(
                conversation_id=conversation_id,
                role="ASSISTANT",
                content=full_answer,
            )

            done_payload = json.dumps({"type": "done"})
            yield f"data: {done_payload}\n\n"

        except Exception as error:
            error_payload = json.dumps(
                {
                    "type": "error",
                    "message": str(error),
                }
            )

            yield f"data: {error_payload}\n\n"