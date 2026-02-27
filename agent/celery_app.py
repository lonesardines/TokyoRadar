"""Celery application for the agent worker."""

from celery import Celery

from tokyoradar_shared.config import settings

app = Celery(
    "agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tokyo",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "agent.tasks.*": {"queue": "agent"},
    },
)

app.autodiscover_tasks(["agent"])
