from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai.rag import ask_question
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

    result = ask_question(request.question)

    message_repository.create(
        conversation_id=request.conversation_id,
        role="ASSISTANT",
        content=result["answer"],
    )

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
    )