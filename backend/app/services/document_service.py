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
        self.document_repository = DocumentRepository(db)

    def validate_file(self, file: UploadFile) -> None:
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise UnsupportedFileTypeError()

        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > MAX_FILE_SIZE:
            raise FileTooLargeError()

    def upload_document(self, file: UploadFile, current_user: User):
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

    def list_documents(self, current_user: User):
        return self.document_repository.get_by_user(current_user.id)

    def get_document(self, document_id: int, current_user: User):
        document = self.document_repository.get_by_id(document_id)

        if not document:
            raise ValueError("Document not found")

        if document.uploaded_by != current_user.id:
            raise ValueError("You are not authorized to access this document")

        return document

    def delete_document(self, document_id: int, current_user: User):
        document = self.document_repository.get_by_id(document_id)

        if not document:
            raise ValueError("Document not found")

        if document.uploaded_by != current_user.id:
            raise ValueError("You are not authorized to delete this document")

        if os.path.exists(document.file_path):
            os.remove(document.file_path)
            
        VectorStore().delete_document(document.id)

        self.document_repository.delete(document)

        return {
            "message": "Document deleted successfully"
        }