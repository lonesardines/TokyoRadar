from celery import Celery

from tokyoradar_shared.config import settings

app = Celery(
    "scraper",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    task_routes={
        "scraper.tasks.*": {"queue": "scraper"},
    },
)

app.autodiscover_tasks(["scraper"])
