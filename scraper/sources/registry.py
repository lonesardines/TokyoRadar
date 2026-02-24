from dataclasses import dataclass

from scraper.sources.base import BrandScraper
from scraper.sources.shopify import ShopifyBrandScraper


@dataclass
class ScraperConfig:
    scraper_class: type[BrandScraper]
    domain: str
    source: str  # identifier for ScrapeJob.source


SCRAPER_REGISTRY: dict[str, ScraperConfig] = {
    "nanamica": ScraperConfig(
        scraper_class=ShopifyBrandScraper,
        domain="us.nanamica.com",
        source="shopify:us.nanamica.com",
    ),
}


def get_scraper(brand_slug: str, proxy_url: str | None = None) -> BrandScraper:
    """Get a configured scraper instance for the given brand slug."""
    config = SCRAPER_REGISTRY.get(brand_slug)
    if config is None:
        raise ValueError(f"No scraper configured for brand: {brand_slug}")
    return config.scraper_class(domain=config.domain, proxy_url=proxy_url)


def get_scraper_config(brand_slug: str) -> ScraperConfig | None:
    return SCRAPER_REGISTRY.get(brand_slug)


def list_supported_brands() -> list[str]:
    return list(SCRAPER_REGISTRY.keys())
