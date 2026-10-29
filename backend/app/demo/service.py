"""Throw-away guest sessions for the public demo."""

import io
import logging
import pathlib
import secrets
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session
from starlette.datastructures import Headers

from app.core.security.jwt import create_access_token
from app.core.security.password import hash_password
from app.core.settings import settings
from app.demo.pdf import build_pdf
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.user_repository import UserRepository
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService

logger = logging.getLogger(__name__)

SAMPLES_DIR = pathlib.Path(__file__).parent / "samples"
DEMO_CONVERSATION_TITLE = "Acme Cloud support (demo)"
PAGE_MARKER = "---PAGE---"
# Expired guests purged per new session, so cleanup never blocks a visitor long.
PURGE_BATCH = 10


def _pages(raw: str) -> list[str]:
    """Split a sample file into pages; text before the first marker is a header
    that belongs on page one."""
    preamble, _, rest = raw.partition(PAGE_MARKER)
    pages = [p.strip() for p in rest.split(PAGE_MARKER) if p.strip()]
    if not pages:
        return [preamble.strip()]
    pages[0] = f"{preamble.strip()}\n\n{pages[0]}".strip()
    return pages


def _sample_upload(path: pathlib.Path) -> UploadFile:
    pdf = build_pdf(_pages(path.read_text()))
    return UploadFile(
        file=io.BytesIO(pdf),
        filename=f"{path.stem}.pdf",
        headers=Headers({"content-type": "application/pdf"}),
    )


class DemoService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    def create_session(self) -> tuple[str, int]:
        """Create a guest user with a sample conversation; return (token, id)."""
        # Housekeeping must never stop a visitor from getting a session.
        try:
            self.purge_expired()
        except Exception:
            self.db.rollback()
            logger.exception("demo purge failed; continuing without cleanup")

        user = self.user_repository.create(
            full_name="Demo Visitor",
            email=f"demo-{uuid4().hex[:12]}@demo.example.com",
            # Nobody ever logs in with this: access is by the issued token only.
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            is_demo=True,
        )
        conversation = ConversationRepository(self.db).create(
            title=DEMO_CONVERSATION_TITLE, user_id=user.id
        )

        documents = DocumentService(self.db)
        for path in sorted(SAMPLES_DIR.glob("*.txt")):
            documents.upload_document(_sample_upload(path), conversation.id, user)

        logger.info("demo session created user_id=%s", user.id)
        return create_access_token({"sub": user.email}), conversation.id

    def purge_expired(self, limit: int = PURGE_BATCH) -> int:
        """Delete guests older than the TTL, with everything they own."""
        cutoff = datetime.utcnow() - timedelta(hours=settings.DEMO_USER_TTL_HOURS)
        expired = self.user_repository.get_expired_demo_users(cutoff, limit)

        for user in expired:
            conversations = ConversationRepository(self.db).get_by_user(user.id)
            for conversation in conversations:
                ConversationService(self.db).delete_conversation(conversation.id, user)
            self.user_repository.delete(user)

        if expired:
            logger.info("purged %s expired demo user(s)", len(expired))
        return len(expired)
