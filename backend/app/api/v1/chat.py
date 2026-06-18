from fastapi import APIRouter, Depends

from app.ai.rag import ask_question
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["Chat"],
)


@router.post("/ask", response_model=ChatResponse)
def ask(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    result = ask_question(request.question)

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
    )