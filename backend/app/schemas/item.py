from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PriceListingResponse(BaseModel):
    id: int
    retailer_slug: str
    retailer_name: str
    price_jpy: int | None = None
    price_usd: Decimal | None = None
    in_stock: bool = True
    available_sizes: list[str] | None = None
    url: str | None = None
    last_checked_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemResponse(BaseModel):
    id: int
    brand_id: int
    collection_id: int | None = None
    name_en: str
    name_ja: str | None = None
    item_type: str | None = None
    price_jpy: int | None = None
    price_usd: Decimal | None = None
    compare_at_price_usd: Decimal | None = None
    material: str | None = None
    sizes: list[str] | None = None
    primary_image_url: str | None = None
    source_url: str | None = None
    external_id: str | None = None
    handle: str | None = None
    vendor: str | None = None
    product_type_raw: str | None = None
    tags: list[str] | None = None
    colors: list[str] | None = None
    season_code: str | None = None
    sku: str | None = None
    in_stock: bool | None = None
    price_listings: list[PriceListingResponse] = []
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemDetailResponse(ItemResponse):
    body_html_raw: str | None = None
    shopify_data: dict | None = None


class ItemListResponse(BaseModel):
    data: list[ItemResponse]
    total: int
    page: int
    per_page: int
