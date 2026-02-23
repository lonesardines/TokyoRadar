"""ZOZOTOWN (zozo.jp) scraper.

Scrapes product listings and pricing data from Japan's largest fashion e-commerce.
"""

import httpx


class ZozotownScraper:
    BASE_URL = "https://zozo.jp"

    def __init__(self, proxy_url: str | None = None):
        self.proxy_url = proxy_url

    async def fetch_brand_products(self, brand_slug: str, page: int = 1) -> list[dict]:
        """Fetch product listings for a brand."""
        # TODO: Phase 2 implementation
        raise NotImplementedError

    async def fetch_product_detail(self, product_id: str) -> dict:
        """Fetch detailed product information."""
        # TODO: Phase 2 implementation
        raise NotImplementedError
