from datetime import datetime

from pydantic import BaseModel


class ConversationCreateRequest(BaseModel):
    question: str


class ConversationUpdateRequest(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: int
    title: str
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True