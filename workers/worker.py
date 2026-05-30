import os

from redis import Redis
from rq import Worker

QUEUES = [
    "document_processing",
    "research",
    "curriculum",
    "consolidation",
    "resource_generation",
]


def main() -> None:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    connection = Redis.from_url(redis_url)
    worker = Worker(QUEUES, connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
