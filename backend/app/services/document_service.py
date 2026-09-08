import os
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.ai.chunker import TextChunker
from app.ai.parser import PDFParser
from app.ai.vector_store import VectorStore
from app.core.authz import require_owned_conversation, require_owned_document
from app.core.exceptions.document import (
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.models.user import User
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository

UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
_COPY_CHUNK = 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "image/png": "png",
    "image/jpeg": "jpg",
}

# Leading "magic" bytes for each accepted type. The browser-supplied
# content_type is trivially spoofed, so we sniff the actual file header and
# require it to match the declared type.
_MAGIC_BYTES: dict[str, tuple[bytes, ...]] = {
    "pdf": (b"%PDF-",),
    "docx": (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"),  # zip container
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
}


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
        self.conversation_repository = ConversationRepository(db)
        self.document_repository = DocumentRepository(db)

    def validate_file(self, file: UploadFile) -> str:
        """Validate type and size, returning the resolved file extension."""
        extension = ALLOWED_CONTENT_TYPES.get(file.content_type)

        if extension is None:
            raise UnsupportedFileTypeError()

        header = file.file.read(8)
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if not any(header.startswith(sig) for sig in _MAGIC_BYTES[extension]):
            raise UnsupportedFileTypeError(
                "File content does not match its declared type"
            )

        if file_size == 0:
            raise UnsupportedFileTypeError("Uploaded file is empty")

        if file_size > MAX_FILE_SIZE:
            raise FileTooLargeError()

        return extension

    def validate_conversation_access(self, conversation_id: int, current_user: User):
        return require_owned_conversation(self.db, conversation_id, current_user.id)

    def _write_to_disk(self, file: UploadFile, file_path: str) -> None:
        written = 0
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(_COPY_CHUNK):
                written += len(chunk)
                if written > MAX_FILE_SIZE:
                    buffer.close()
                    os.remove(file_path)
                    raise FileTooLargeError()
                buffer.write(chunk)

    def upload_document(
        self,
        file: UploadFile,
        conversation_id: int,
        current_user: User,
    ):
        self.validate_conversation_access(conversation_id, current_user)
        file_extension = self.validate_file(file)

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        unique_filename = f"{uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        self._write_to_disk(file, file_path)

        document = self.document_repository.create(
            filename=file.filename,
            file_type=file_extension,
            file_path=file_path,
            uploaded_by=current_user.id,
            conversation_id=conversation_id,
        )

        try:
            document = self.document_repository.update_status(document, "PROCESSING")

            if file_extension == "pdf":
                pages = PDFParser.extract_pages(file_path)
                chunks = TextChunker.chunk_pages(pages)

                VectorStore().add_document(
                    document_id=document.id,
                    chunks=chunks,
                    user_id=current_user.id,
                    conversation_id=conversation_id,
                    filename=file.filename,
                )

            document = self.document_repository.update_status(document, "READY")

        except Exception:
            document = self.document_repository.update_status(document, "FAILED")
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
        return require_owned_document(
            self.db, document_id, current_user.id, conversation_id
        )

    def delete_document(
        self,
        document_id: int,
        conversation_id: int,
        current_user: User,
    ):
        document = require_owned_document(
            self.db, document_id, current_user.id, conversation_id
        )

        self.delete_document_record(document)

        return {"message": "Document deleted successfully"}

    def delete_document_record(self, document):
        if os.path.exists(document.file_path):
            os.remove(document.file_path)

        VectorStore().delete_document(document.id, user_id=document.uploaded_by)

        self.document_repository.delete(document)
