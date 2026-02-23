from scraper.celery_app import app


@app.task(name="scraper.tasks.scrape_fashion_press")
def scrape_fashion_press():
    """Scrape latest articles from Fashion Press (fashionpress.net)."""
    # TODO: Phase 2 implementation
    return {"status": "not_implemented", "source": "fashion_press"}


@app.task(name="scraper.tasks.scrape_zozotown")
def scrape_zozotown(brand_slug: str | None = None):
    """Scrape product listings from ZOZOTOWN."""
    # TODO: Phase 2 implementation
    return {"status": "not_implemented", "source": "zozotown", "brand_slug": brand_slug}
