from pydantic import BaseModel


class ChatRequest(BaseModel):
    conversation_id: int
    question: str


class SourceResponse(BaseModel):
    document_id: int | None = None
    conversation_id: int | None = None
    chunk_index: int | None = None
    filename: str | None = None
    page_number: int | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]
