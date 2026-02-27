"""Retailer-brand registry: which brands are available at which retailers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetailerSource:
    """A retailer that carries a specific brand."""
    retailer_slug: str
    domain: str
    scraper_type: str  # "shopify" | "generic" | "sitemap"
    tier: str  # "official" | "green" | "yellow" | "red"
    path_prefix: str | None = None
    search_url_template: str | None = None
    notes: str | None = None


RETAILER_BRAND_REGISTRY: dict[str, list[RetailerSource]] = {
    "nanamica": [
        RetailerSource(
            retailer_slug="nanamica-us",
            domain="us.nanamica.com",
            scraper_type="shopify",
            tier="official",
            notes="Official US Shopify store",
        ),
        RetailerSource(
            retailer_slug="end-clothing",
            domain="www.endclothing.com",
            scraper_type="generic",
            tier="green",
            search_url_template="https://www.endclothing.com/us/brands/nanamica",
            notes="END. Clothing — brand page",
        ),
        RetailerSource(
            retailer_slug="ssense",
            domain="www.ssense.com",
            scraper_type="generic",
            tier="green",
            search_url_template="https://www.ssense.com/en-us/men/designers/nanamica",
            notes="SSENSE — brand page with JSON-LD product data",
        ),
        RetailerSource(
            retailer_slug="mr-porter",
            domain="www.mrporter.com",
            scraper_type="sitemap",
            tier="green",
            notes="Mr Porter — Akamai-protected, use scrape_sitemap tool",
        ),
    ],
}


def get_retailer_sources(brand_slug: str) -> list[RetailerSource]:
    """Get all retailer sources for a brand."""
    return RETAILER_BRAND_REGISTRY.get(brand_slug, [])


def get_official_source(brand_slug: str) -> RetailerSource | None:
    """Get the official store source for a brand."""
    for src in get_retailer_sources(brand_slug):
        if src.tier == "official":
            return src
    return None


def list_registered_brands() -> list[str]:
    """List all brands with retailer registry entries."""
    return list(RETAILER_BRAND_REGISTRY.keys())
