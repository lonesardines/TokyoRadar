import logging
from dataclasses import asdict
from datetime import datetime, timezone

from scraper.celery_app import app
from scraper.sources.registry import get_scraper, get_scraper_config
from scraper.validation import validate_products

from tokyoradar_shared.database import SessionLocal
from tokyoradar_shared.models import Brand, Item, Media, ScrapeJob

logger = logging.getLogger(__name__)


@app.task(name="scraper.tasks.trigger_brand_scrape", bind=True)
def trigger_brand_scrape(self, brand_slug: str) -> dict:
    """Create a ScrapeJob and kick off the scraping pipeline."""
    config = get_scraper_config(brand_slug)
    if config is None:
        return {"error": f"No scraper configured for brand: {brand_slug}"}

    db = SessionLocal()
    try:
        brand = db.query(Brand).filter(Brand.slug == brand_slug).first()
        if not brand:
            return {"error": f"Brand not found: {brand_slug}"}

        job = ScrapeJob(
            brand_id=brand.id,
            source=config.source,
            status="pending",
            celery_task_id=self.request.id,
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        job_id = job.id
    finally:
        db.close()

    # Chain: scrape -> validate & store
    scrape_brand_products.apply_async(
        args=[brand_slug, job_id],
        link=validate_and_store.s(brand_slug, job_id),
    )

    return {"job_id": job_id, "brand_slug": brand_slug, "status": "started"}


@app.task(name="scraper.tasks.scrape_brand_products")
def scrape_brand_products(brand_slug: str, job_id: int) -> list[dict]:
    """Scrape products from a brand's website. Returns list of raw product dicts."""
    db = SessionLocal()
    try:
        job = db.query(ScrapeJob).get(job_id)
        if job:
            job.status = "scraping"
            job.started_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()

    try:
        with get_scraper(brand_slug) as scraper:
            raw_products = scraper.scrape_products()

        # Convert dataclass to dict for JSON serialization
        result = []
        for rp in raw_products:
            d = asdict(rp)
            # Convert Decimal to str for JSON
            for key in ("price_usd", "compare_at_price_usd"):
                if d.get(key) is not None:
                    d[key] = str(d[key])
            result.append(d)

        db = SessionLocal()
        try:
            job = db.query(ScrapeJob).get(job_id)
            if job:
                job.items_found = len(result)
                db.commit()
        finally:
            db.close()

        logger.info("Scraped %d products for %s (job %d)", len(result), brand_slug, job_id)
        return result

    except Exception as e:
        db = SessionLocal()
        try:
            job = db.query(ScrapeJob).get(job_id)
            if job:
                job.status = "failed"
                job.errors = {"scrape_error": str(e)}
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        finally:
            db.close()
        raise


@app.task(name="scraper.tasks.validate_and_store")
def validate_and_store(raw_products: list[dict], brand_slug: str, job_id: int) -> dict:
    """Validate scraped products and upsert into the database."""
    db = SessionLocal()
    try:
        job = db.query(ScrapeJob).get(job_id)
        if job:
            job.status = "validating"
            db.commit()

        brand = db.query(Brand).filter(Brand.slug == brand_slug).first()
        if not brand:
            if job:
                job.status = "failed"
                job.errors = {"error": f"Brand not found: {brand_slug}"}
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
            return {"error": f"Brand not found: {brand_slug}"}

        # Validate
        validated = validate_products(raw_products, brand_slug)

        if job:
            job.status = "storing"
            db.commit()

        # Upsert valid items
        items_stored = 0
        items_flagged = 0
        all_flags = []

        for vp in validated:
            if vp.flags:
                items_flagged += 1
                all_flags.append({
                    "external_id": vp.external_id,
                    "name": vp.name,
                    "flags": [
                        {"field": f.field, "severity": f.severity, "message": f.message}
                        for f in vp.flags
                    ],
                })

            if not vp.is_valid:
                continue

            raw = vp.data

            # Upsert: find by brand_id + external_id
            item = db.query(Item).filter(
                Item.brand_id == brand.id,
                Item.external_id == raw.get("external_id"),
            ).first()

            if item is None:
                item = Item(brand_id=brand.id, external_id=raw.get("external_id"))
                db.add(item)

            # Update fields
            item.name_en = raw.get("name", "")
            item.handle = raw.get("handle")
            item.vendor = raw.get("vendor")
            item.product_type_raw = raw.get("product_type")
            item.item_type = (raw.get("product_type") or "").lower().strip() or None
            item.tags = raw.get("tags")
            item.colors = raw.get("colors")
            item.sizes = raw.get("sizes")
            item.body_html_raw = raw.get("body_html")
            item.season_code = raw.get("season_code")
            item.sku = raw.get("sku")
            item.in_stock = raw.get("in_stock", True)
            item.primary_image_url = raw.get("primary_image_url")
            item.source_url = raw.get("source_url")
            item.material = raw.get("material")
            item.shopify_data = raw.get("raw_data")

            if raw.get("price_usd") is not None:
                item.price_usd = raw["price_usd"]
            if raw.get("compare_at_price_usd") is not None:
                item.compare_at_price_usd = raw["compare_at_price_usd"]

            items_stored += 1

            # Upsert media for images
            for idx, img_url in enumerate(raw.get("image_urls", [])):
                existing = db.query(Media).filter(
                    Media.entity_type == "item",
                    Media.entity_id == item.id if item.id else None,
                    Media.url == img_url,
                ).first()
                if existing is None and item.id:
                    media = Media(
                        entity_type="item",
                        entity_id=item.id,
                        url=img_url,
                        media_type="image",
                        sort_order=idx,
                    )
                    db.add(media)

        db.flush()

        # Now handle media for newly created items (which now have IDs)
        for vp in validated:
            if not vp.is_valid:
                continue
            raw = vp.data
            item = db.query(Item).filter(
                Item.brand_id == brand.id,
                Item.external_id == raw.get("external_id"),
            ).first()
            if item:
                for idx, img_url in enumerate(raw.get("image_urls", [])):
                    existing = db.query(Media).filter(
                        Media.entity_type == "item",
                        Media.entity_id == item.id,
                        Media.url == img_url,
                    ).first()
                    if existing is None:
                        media = Media(
                            entity_type="item",
                            entity_id=item.id,
                            url=img_url,
                            media_type="image",
                            sort_order=idx,
                        )
                        db.add(media)

        # Update job
        if job:
            job.status = "completed"
            job.items_stored = items_stored
            job.items_flagged = items_flagged
            job.flags = all_flags if all_flags else None
            job.completed_at = datetime.now(timezone.utc)

        db.commit()

        logger.info(
            "Job %d complete: %d stored, %d flagged for %s",
            job_id, items_stored, items_flagged, brand_slug,
        )
        return {
            "job_id": job_id,
            "items_stored": items_stored,
            "items_flagged": items_flagged,
            "status": "completed",
        }

    except Exception as e:
        db.rollback()
        try:
            job = db.query(ScrapeJob).get(job_id)
            if job:
                job.status = "failed"
                job.errors = {"store_error": str(e)}
                job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            pass
        raise
    finally:
        db.close()


# Keep legacy stubs for backward compatibility
@app.task(name="scraper.tasks.scrape_fashion_press")
def scrape_fashion_press():
    """Scrape latest articles from Fashion Press (fashionpress.net)."""
    return {"status": "not_implemented", "source": "fashion_press"}


@app.task(name="scraper.tasks.scrape_zozotown")
def scrape_zozotown(brand_slug: str | None = None):
    """Scrape product listings from ZOZOTOWN."""
    return {"status": "not_implemented", "source": "zozotown", "brand_slug": brand_slug}
