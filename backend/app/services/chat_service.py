import json
import logging
from typing import Generator

from sqlalchemy.orm import Session

from app.ai.llm import stream_answer
from app.ai.rag import ask_question, build_context
from app.core.authz import require_owned_conversation
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository

logger = logging.getLogger(__name__)

GENERIC_STREAM_ERROR = "Something went wrong while generating the response."


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.conversation_repository = ConversationRepository(db)
        self.message_repository = MessageRepository(db)

    def validate_conversation_access(self, conversation_id: int, current_user: User):
        return require_owned_conversation(self.db, conversation_id, current_user.id)

    def build_conversation_history(self, conversation_id: int) -> str:
        history = self.message_repository.get_recent_messages(conversation_id)

        return "\n".join(
            f"{message.role}: {message.content}"
            for message in reversed(history)
        )

    def ask(self, conversation_id: int, question: str, current_user: User):
        self.validate_conversation_access(conversation_id, current_user)

        self.message_repository.create(conversation_id, "USER", question)

        conversation_history = self.build_conversation_history(conversation_id)

        result = ask_question(
            question=question,
            user_id=current_user.id,
            conversation_id=conversation_id,
            conversation_history=conversation_history,
        )

        self.message_repository.create(conversation_id, "ASSISTANT", result["answer"])

        return result

    def stream(
        self,
        conversation_id: int,
        question: str,
        current_user: User,
    ) -> Generator[str, None, None]:
        # Defense in depth: the endpoint already checks ownership, but the
        # generator re-validates so it can never run unscoped.
        self.validate_conversation_access(conversation_id, current_user)

        self.message_repository.create(conversation_id, "USER", question)

        conversation_history = self.build_conversation_history(conversation_id)

        full_answer = ""

        try:
            context, sources = build_context(
                question=question,
                user_id=current_user.id,
                conversation_id=conversation_id,
            )

            sources_payload = json.dumps({
                "type": "sources",
                "sources": sources,
            })

            yield f"data: {sources_payload}\n\n"

            for token in stream_answer(
                question=question,
                context=context,
                conversation_history=conversation_history,
            ):
                full_answer += token

                token_payload = json.dumps({
                    "type": "token",
                    "content": token,
                })

                yield f"data: {token_payload}\n\n"

            self.message_repository.create(
                conversation_id=conversation_id,
                role="ASSISTANT",
                content=full_answer,
            )

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception:
            logger.exception("Streaming chat failed for conversation %s", conversation_id)

            error_payload = json.dumps({
                "type": "error",
                "message": GENERIC_STREAM_ERROR,
            })

            yield f"data: {error_payload}\n\n"
