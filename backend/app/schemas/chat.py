from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class SourceResponse(BaseModel):
    document_id: int
    chunk_index: int


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]