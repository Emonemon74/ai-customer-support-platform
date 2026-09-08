import json
import logging
from collections.abc import Generator

from sqlalchemy.orm import Session

from app.ai.llm import FALLBACK_ANSWER, stream_answer
from app.ai.rag import ask_question, build_context, reconcile_sources
from app.core.authz import require_owned_conversation
from app.core.observability import Timer, metrics, set_context
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

    def _log_answer(self, conversation_id: int, stats: dict, answer: str) -> None:
        abstained = answer.strip() == FALLBACK_ANSWER
        outcome = "abstained" if abstained else "answered"

        metrics.inc("chat_answers_total", outcome=outcome)
        if "retrieval_ms" in stats:
            metrics.observe("chat_retrieval_ms", stats["retrieval_ms"])
        if "llm_ms" in stats:
            metrics.observe("chat_llm_ms", stats["llm_ms"])
        if stats.get("total_tokens"):
            metrics.inc("chat_llm_tokens_total", stats["total_tokens"])

        logger.info(
            "chat %s conversation_id=%s retrieval_ms=%.1f llm_ms=%.1f "
            "context_chunks=%s prompt_tokens=%s completion_tokens=%s answer_chars=%s",
            outcome,
            conversation_id,
            stats.get("retrieval_ms", 0.0),
            stats.get("llm_ms", 0.0),
            stats.get("context_chunks", 0),
            stats.get("prompt_tokens", "-"),
            stats.get("completion_tokens", "-"),
            len(answer),
        )

    def ask(self, conversation_id: int, question: str, current_user: User):
        self.validate_conversation_access(conversation_id, current_user)
        set_context(user_id=current_user.id, conversation_id=conversation_id)

        self.message_repository.create(conversation_id, "USER", question)

        conversation_history = self.build_conversation_history(conversation_id)

        stats: dict = {}
        result = ask_question(
            question=question,
            user_id=current_user.id,
            conversation_id=conversation_id,
            conversation_history=conversation_history,
            stats=stats,
        )

        self.message_repository.create(conversation_id, "ASSISTANT", result["answer"])
        self._log_answer(conversation_id, stats, result["answer"])

        return result

    def stream(
        self,
        conversation_id: int,
        question: str,
        current_user: User,
    ) -> Generator[str]:
        # Defense in depth: the endpoint already checks ownership, but the
        # generator re-validates so it can never run unscoped.
        self.validate_conversation_access(conversation_id, current_user)
        set_context(user_id=current_user.id, conversation_id=conversation_id)

        self.message_repository.create(conversation_id, "USER", question)

        conversation_history = self.build_conversation_history(conversation_id)

        full_answer = ""
        stats: dict = {}

        try:
            with Timer() as retrieval:
                context, sources = build_context(
                    question=question,
                    user_id=current_user.id,
                    conversation_id=conversation_id,
                )
            stats["retrieval_ms"] = retrieval.ms
            stats["context_chunks"] = len(sources)

            sources_payload = json.dumps({
                "type": "sources",
                "sources": sources,
            })

            yield f"data: {sources_payload}\n\n"

            with Timer() as llm:
                for token in stream_answer(
                    question=question,
                    context=context,
                    conversation_history=conversation_history,
                    stats=stats,
                ):
                    full_answer += token

                    token_payload = json.dumps({
                        "type": "token",
                        "content": token,
                    })

                    yield f"data: {token_payload}\n\n"
            stats["llm_ms"] = llm.ms

            self.message_repository.create(
                conversation_id=conversation_id,
                role="ASSISTANT",
                content=full_answer,
            )

            # The first sources event was the retrieved set; now that we have
            # the full answer, replace it with the ones actually cited.
            final_sources = reconcile_sources(full_answer, sources)
            yield f"data: {json.dumps({'type': 'sources', 'sources': final_sources})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

            self._log_answer(conversation_id, stats, full_answer)

        except Exception:
            metrics.inc("chat_answers_total", outcome="error")
            logger.exception("Streaming chat failed for conversation %s", conversation_id)

            error_payload = json.dumps({
                "type": "error",
                "message": GENERIC_STREAM_ERROR,
            })

            yield f"data: {error_payload}\n\n"
