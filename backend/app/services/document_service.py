import os
import shutil
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.ai.chunker import TextChunker
from app.ai.parser import PDFParser
from app.ai.vector_store import VectorStore
from app.core.exceptions.document import (
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository


UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/png": "png",
    "image/jpeg": "jpg",
}


class DocumentService:
    def __init__(self, db: Session):
        self.conversation_repository = ConversationRepository(db)
        self.document_repository = DocumentRepository(db)

    def validate_file(self, file: UploadFile) -> None:
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise UnsupportedFileTypeError()

        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise FileTooLargeError()

    def validate_conversation_access(self, conversation_id: int, current_user: User):
        conversation = self.conversation_repository.get_by_id(conversation_id)

        if not conversation:
            raise ValueError("Conversation not found")

        if conversation.user_id != current_user.id:
            raise ValueError("You are not authorized to access this conversation")

        return conversation

    def upload_document(
        self,
        file: UploadFile,
        conversation_id: int,
        current_user: User,
    ):
        self.validate_conversation_access(conversation_id, current_user)
        self.validate_file(file)

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        file_extension = ALLOWED_CONTENT_TYPES[file.content_type]
        unique_filename = f"{uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document = self.document_repository.create(
            filename=file.filename,
            file_type=file_extension,
            file_path=file_path,
            uploaded_by=current_user.id,
            conversation_id=conversation_id,
        )

        try:
            document = self.document_repository.update_status(
                document,
                "PROCESSING",
            )

            if file_extension == "pdf":
                text = PDFParser.extract_text(file_path)
                chunks = TextChunker.chunk(text)

                VectorStore().add_document(
                    document_id=document.id,
                    chunks=chunks,
                    user_id=current_user.id,
                    conversation_id=conversation_id,
                    filename=file.filename,
                )

            document = self.document_repository.update_status(
                document,
                "READY",
            )

        except Exception:
            document = self.document_repository.update_status(
                document,
                "FAILED",
            )
            raise

        return document

    def list_documents(self, conversation_id: int, current_user: User):
        self.validate_conversation_access(conversation_id, current_user)

        return self.document_repository.get_by_conversation(
            user_id=current_user.id,
            conversation_id=conversation_id,
        )

    def get_document(
        self,
        document_id: int,
        conversation_id: int,
        current_user: User,
    ):
        self.validate_conversation_access(conversation_id, current_user)
        document = self.document_repository.get_by_id(document_id)

        if not document:
            raise ValueError("Document not found")

        if (
            document.uploaded_by != current_user.id
            or document.conversation_id != conversation_id
        ):
            raise ValueError("You are not authorized to access this document")

        return document

    def delete_document(
        self,
        document_id: int,
        conversation_id: int,
        current_user: User,
    ):
        self.validate_conversation_access(conversation_id, current_user)
        document = self.document_repository.get_by_id(document_id)

        if not document:
            raise ValueError("Document not found")

        if (
            document.uploaded_by != current_user.id
            or document.conversation_id != conversation_id
        ):
            raise ValueError("You are not authorized to delete this document")

        self.delete_document_record(document)

        return {
            "message": "Document deleted successfully"
        }

    def delete_document_record(self, document):
        if os.path.exists(document.file_path):
            os.remove(document.file_path)

        VectorStore().delete_document(document.id)

        self.document_repository.delete(document)
