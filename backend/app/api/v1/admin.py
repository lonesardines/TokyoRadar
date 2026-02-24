from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Brand, ScrapeJob
from app.schemas.scrape_job import (
    ScrapeJobListResponse,
    ScrapeJobResponse,
    ScrapeJobTrigger,
)
from scraper.sources.registry import list_supported_brands

router = APIRouter()

# Send-only Celery client — does not start a worker, only dispatches tasks
celery_app = Celery(broker=settings.REDIS_URL)


@router.post("/scrape-jobs", response_model=ScrapeJobResponse, status_code=201)
def trigger_scrape(
    body: ScrapeJobTrigger,
    db: Session = Depends(get_db),
) -> ScrapeJobResponse:
    brand = db.query(Brand).filter(Brand.slug == body.brand_slug).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    supported = list_supported_brands()
    if body.brand_slug not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"No scraper configured for '{body.brand_slug}'. Supported: {supported}",
        )

    # Dispatch to scraper worker via Celery send_task (decoupled)
    result = celery_app.send_task(
        "scraper.tasks.trigger_brand_scrape",
        args=[body.brand_slug],
        queue="scraper",
    )

    # Create a job record here so we can return it immediately
    from scraper.sources.registry import get_scraper_config

    config = get_scraper_config(body.brand_slug)
    job = ScrapeJob(
        brand_id=brand.id,
        source=config.source if config else "unknown",
        status="pending",
        celery_task_id=result.id,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return ScrapeJobResponse.model_validate(job)


@router.get("/scrape-jobs", response_model=ScrapeJobListResponse)
def list_scrape_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = None,
    brand_slug: str | None = None,
    db: Session = Depends(get_db),
) -> ScrapeJobListResponse:
    query = db.query(ScrapeJob)

    if status:
        query = query.filter(ScrapeJob.status == status)

    if brand_slug:
        brand = db.query(Brand).filter(Brand.slug == brand_slug).first()
        if brand:
            query = query.filter(ScrapeJob.brand_id == brand.id)
        else:
            return ScrapeJobListResponse(data=[], total=0, page=page, per_page=per_page)

    total = query.count()
    jobs = query.order_by(ScrapeJob.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return ScrapeJobListResponse(
        data=[ScrapeJobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/scrape-jobs/{job_id}", response_model=ScrapeJobResponse)
def get_scrape_job(
    job_id: int,
    db: Session = Depends(get_db),
) -> ScrapeJobResponse:
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Scrape job not found")
    return ScrapeJobResponse.model_validate(job)


@router.get("/supported-brands")
def get_supported_brands() -> dict:
    return {"brands": list_supported_brands()}
