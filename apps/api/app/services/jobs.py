from __future__ import annotations

from dataclasses import dataclass

from redis import Redis
from redis.exceptions import RedisError
from rq import Queue

from app.core.config import settings

QUEUE_NAMES = {
    "document_processing",
    "research",
    "curriculum",
    "consolidation",
    "resource_generation",
}


@dataclass(frozen=True)
class EnqueuedJob:
    id: str
    queue_name: str


class QueueUnavailableError(RuntimeError):
    pass


def enqueue_rq_job(queue_name: str, function_path: str, *args: object) -> EnqueuedJob:
    if queue_name not in QUEUE_NAMES:
        raise ValueError(f"Cola no soportada: {queue_name}")
    try:
        connection = Redis.from_url(settings.redis_url)
        connection.ping()
        queue = Queue(queue_name, connection=connection)
        job = queue.enqueue(function_path, *args)
    except RedisError as exc:
        raise QueueUnavailableError(
            "Redis no esta disponible. Arranca el stack Docker o configura REDIS_URL para usar workers RQ."
        ) from exc
    return EnqueuedJob(id=job.id, queue_name=queue_name)
