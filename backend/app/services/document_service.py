import hashlib
import os
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.ai import cache as retrieval_cache
from app.ai.chunker import TextChunker
from app.ai.parser import PDFParser
from app.ai.vector_store import VectorStore
from app.core.authz import require_owned_conversation, require_owned_document
from app.core.exceptions.document import (
    DuplicateDocumentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.core.logging.logger import logger
from app.core.observability import Timer, metrics, set_context
from app.core.settings import settings
from app.models.document import (
    STATUS_FAILED,
    STATUS_PROCESSING,
    STATUS_QUEUED,
    STATUS_READY,
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

    def _write_to_disk(self, file: UploadFile, file_path: str) -> str:
        """Stream the upload to disk, returning its SHA-256 hex digest."""
        digest = hashlib.sha256()
        written = 0
        with open(file_path, "wb") as buffer:
            while chunk := file.file.read(_COPY_CHUNK):
                written += len(chunk)
                if written > MAX_FILE_SIZE:
                    buffer.close()
                    os.remove(file_path)
                    raise FileTooLargeError()
                digest.update(chunk)
                buffer.write(chunk)
        return digest.hexdigest()

    def upload_document(
        self,
        file: UploadFile,
        conversation_id: int,
        current_user: User,
    ):
        """Persist the raw file and queue it for processing.

        Returns immediately with a ``QUEUED`` document -- parsing, chunking and
        embedding happen in a background job (or inline when
        ``DOCUMENT_QUEUE_ASYNC`` is off).
        """
        self.validate_conversation_access(conversation_id, current_user)
        file_extension = self.validate_file(file)

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        unique_filename = f"{uuid4()}.{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        content_hash = self._write_to_disk(file, file_path)

        existing = self.document_repository.get_by_content_hash(
            conversation_id, content_hash
        )
        if existing is not None:
            os.remove(file_path)
            raise DuplicateDocumentError()

        document = self.document_repository.create(
            filename=file.filename,
            file_type=file_extension,
            file_path=file_path,
            uploaded_by=current_user.id,
            conversation_id=conversation_id,
            content_hash=content_hash,
            status=STATUS_QUEUED,
        )

        self._enqueue(document)

        return document

    def _enqueue(self, document) -> None:
        if settings.DOCUMENT_QUEUE_ASYNC:
            from rq import Retry

            from app.worker.queue import get_document_queue
            from app.worker.tasks import process_document

            get_document_queue().enqueue(
                process_document,
                document.id,
                retry=Retry(
                    max=settings.DOCUMENT_MAX_RETRIES,
                    interval=[10, 30, 60],
                ),
            )
            logger.info("queued document_id=%s for processing", document.id)
        else:
            self.process_document(document.id)

    def process_document(self, document_id: int) -> None:
        """Parse -> chunk -> embed -> index. Idempotent and retry-safe."""
        document = self.document_repository.get_by_id(document_id)

        if document is None:
            logger.warning("process_document: document_id=%s not found", document_id)
            return

        set_context(
            document_id=document.id, conversation_id=document.conversation_id
        )

        if document.status == STATUS_READY:
            return

        self.document_repository.update_status(document, STATUS_PROCESSING)

        try:
            with Timer() as processing:
                chunk_count = 0

                if document.file_type == "pdf":
                    # Clear anything a previous attempt may have indexed so a
                    # retry does not create duplicate chunks.
                    VectorStore().delete_document(
                        document.id, user_id=document.uploaded_by
                    )

                    pages = PDFParser.extract_pages(document.file_path)
                    chunks = TextChunker.chunk_pages(pages)
                    chunk_count = len(chunks)

                    VectorStore().add_document(
                        document_id=document.id,
                        chunks=chunks,
                        user_id=document.uploaded_by,
                        conversation_id=document.conversation_id,
                        filename=document.filename,
                    )

            self.document_repository.update_status(document, STATUS_READY)
            retrieval_cache.bump_conversation(document.conversation_id)

            metrics.inc("document_processing_total", status="ready")
            metrics.observe("document_processing_ms", processing.ms)
            logger.info(
                "document processed document_id=%s chunks=%s (%.0f ms)",
                document.id,
                chunk_count,
                processing.ms,
            )

        except Exception as error:
            self.document_repository.update_status(
                document, STATUS_FAILED, str(error)[:1000]
            )
            metrics.inc("document_processing_total", status="failed")
            metrics.inc("document_processing_failures_total")
            raise

    def retry_document(
        self,
        document_id: int,
        conversation_id: int,
        current_user: User,
    ):
        document = require_owned_document(
            self.db, document_id, current_user.id, conversation_id
        )

        if document.status != STATUS_FAILED:
            return document

        self.document_repository.update_status(document, STATUS_QUEUED)
        self._enqueue(document)

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
        retrieval_cache.bump_conversation(document.conversation_id)

        self.document_repository.delete(document)
