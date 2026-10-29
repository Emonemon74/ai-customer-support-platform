"""RQ queue wiring for asynchronous document ingestion."""

from redis import Redis
from rq import Queue

from app.core.settings import settings

_redis: Redis | None = None


def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.REDIS_URL)
    return _redis


def get_document_queue() -> Queue:
    return Queue(settings.DOCUMENT_QUEUE_NAME, connection=get_redis())
