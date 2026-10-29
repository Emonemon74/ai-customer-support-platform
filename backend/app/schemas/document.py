from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_type: str
    status: str
    failure_reason: str | None = None
    uploaded_by: int
    conversation_id: int
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True
