from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ScrapeJobTrigger(BaseModel):
    brand_slug: str


class ScrapeJobResponse(BaseModel):
    id: int
    brand_id: int
    source: str
    status: str
    celery_task_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    items_found: int | None = None
    items_stored: int | None = None
    items_flagged: int | None = None
    errors: dict | None = None
    flags: dict | None = None
    config: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScrapeJobListResponse(BaseModel):
    data: list[ScrapeJobResponse]
    total: int
    page: int
    per_page: int
