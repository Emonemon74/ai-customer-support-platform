import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.ai.rag import ask_question, stream_question
from app.db.deps import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
)


@router.post("/ask", response_model=ChatResponse)
def ask(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation_repository = ConversationRepository(db)
    message_repository = MessageRepository(db)

    conversation = conversation_repository.get_by_id(request.conversation_id)

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

    message_repository.create(
        conversation_id=request.conversation_id,
        role="USER",
        content=request.question,
    )

    history = message_repository.get_recent_messages(request.conversation_id)

    conversation_history = "\n".join(
        [f"{message.role}: {message.content}" for message in reversed(history)]
    )

    result = ask_question(
        question=request.question,
        conversation_history=conversation_history,
    )

    message_repository.create(
        conversation_id=request.conversation_id,
        role="ASSISTANT",
        content=result["answer"],
    )

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
    )


@router.post("/stream")
def stream_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conversation_repository = ConversationRepository(db)
    message_repository = MessageRepository(db)

    conversation = conversation_repository.get_by_id(request.conversation_id)

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

    message_repository.create(
        conversation_id=request.conversation_id,
        role="USER",
        content=request.question,
    )

    history = message_repository.get_recent_messages(request.conversation_id)

    conversation_history = "\n".join(
        [f"{message.role}: {message.content}" for message in reversed(history)]
    )

    def generate():
        full_answer = ""

        try:
            for token in stream_question(
                question=request.question,
                conversation_history=conversation_history,
            ):
                full_answer += token

                payload = json.dumps({
                    "type": "token",
                    "content": token,
                })

                yield f"data: {payload}\n\n"

            message_repository.create(
                conversation_id=request.conversation_id,
                role="ASSISTANT",
                content=full_answer,
            )

            done_payload = json.dumps({
                "type": "done",
            })

            yield f"data: {done_payload}\n\n"

        except Exception as error:
            error_payload = json.dumps({
                "type": "error",
                "message": str(error),
            })

            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )