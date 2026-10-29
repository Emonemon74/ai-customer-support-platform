"""RQ worker entrypoint: ``python -m app.worker.main``.

Drains the document-ingestion queue. Run alongside the API (the Docker stack
starts it as a separate ``worker`` service).
"""

from rq import Worker

from app.core.logging.logger import logger
from app.core.observability import configure_logging
from app.core.settings import settings
from app.worker.queue import get_redis


def main() -> None:
    configure_logging()
    logger.info("starting RQ worker on queue=%s", settings.DOCUMENT_QUEUE_NAME)
    worker = Worker([settings.DOCUMENT_QUEUE_NAME], connection=get_redis())
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
