from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

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
    chat_service = ChatService(db)

    result = chat_service.ask(
        conversation_id=request.conversation_id,
        question=request.question,
        current_user=current_user,
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
    chat_service = ChatService(db)

    return StreamingResponse(
        chat_service.stream(
            conversation_id=request.conversation_id,
            question=request.question,
            current_user=current_user,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )