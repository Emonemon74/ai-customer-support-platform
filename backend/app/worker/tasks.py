"""Background jobs run by the RQ worker.

Each job opens its own database session -- it runs in a separate process from
the API and must not share SQLAlchemy sessions with it.
"""

from app.core.exceptions.document import NoReadableTextError
from app.core.logging.logger import logger
from app.core.observability import bind_context, new_request_id
from app.db.session import SessionLocal


def process_document(document_id: int) -> None:
    """Parse, chunk, embed and index a document.

    Idempotent: safe to run more than once for the same document (RQ retries,
    a manual retry after a failure). Raises on failure so RQ records the job
    as failed and can retry it, except for files with no readable text, which
    are failed once and never retried.
    """
    from app.services.document_service import DocumentService

    bind_context(request_id=new_request_id(), job_id=f"process_document:{document_id}")
    logger.info("process_document start document_id=%s", document_id)
    db = SessionLocal()
    try:
        DocumentService(db).process_document(document_id)
        logger.info("process_document done document_id=%s", document_id)
    except NoReadableTextError:
        # Already marked FAILED with a readable reason. Retrying the same file
        # cannot change the outcome, so don't let RQ re-run it.
        logger.warning("process_document no readable text document_id=%s", document_id)
    except Exception:
        logger.exception("process_document failed document_id=%s", document_id)
        raise
    finally:
        db.close()
