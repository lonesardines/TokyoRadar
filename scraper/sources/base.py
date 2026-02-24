from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal

import httpx


@dataclass
class RawProduct:
    external_id: str
    name: str
    handle: str | None = None
    vendor: str | None = None
    product_type: str | None = None
    tags: list[str] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)
    sizes: list[str] = field(default_factory=list)
    price_usd: Decimal | None = None
    compare_at_price_usd: Decimal | None = None
    material: str | None = None
    body_html: str | None = None
    season_code: str | None = None
    sku: str | None = None
    in_stock: bool = True
    primary_image_url: str | None = None
    image_urls: list[str] = field(default_factory=list)
    source_url: str | None = None
    raw_data: dict | None = None


class BrandScraper(ABC):
    def __init__(self, domain: str, proxy_url: str | None = None):
        self.domain = domain
        self.proxy_url = proxy_url
        self._client: httpx.Client | None = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=f"https://{self.domain}",
                headers={"User-Agent": "TokyoRadar/1.0"},
                timeout=30.0,
                follow_redirects=True,
                proxy=self.proxy_url,
            )
        return self._client

    @abstractmethod
    def scrape_products(self) -> list[RawProduct]:
        ...

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
