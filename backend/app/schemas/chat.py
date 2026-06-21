from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: int
    question: str


class SourceResponse(BaseModel):
    document_id: int
    chunk_index: int
    filename: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]