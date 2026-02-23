from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BrandBase(BaseModel):
    slug: str
    name_en: str
    name_ja: str | None = None
    designer: str | None = None
    founded_year: int | None = None
    headquarters: str | None = None
    website_jp: str | None = None
    website_us: str | None = None
    has_redirect: bool = False
    style_tags: list[str] | None = None
    price_range: str | None = None
    description_en: str | None = None
    description_ja: str | None = None
    shipping_tier: str | None = None
    buy_guide: dict | None = None
    logo_url: str | None = None


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    slug: str | None = None
    name_en: str | None = None
    name_ja: str | None = None
    designer: str | None = None
    founded_year: int | None = None
    headquarters: str | None = None
    website_jp: str | None = None
    website_us: str | None = None
    has_redirect: bool | None = None
    style_tags: list[str] | None = None
    price_range: str | None = None
    description_en: str | None = None
    description_ja: str | None = None
    shipping_tier: str | None = None
    buy_guide: dict | None = None
    logo_url: str | None = None


class BrandResponse(BrandBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class BrandListResponse(BaseModel):
    data: list[BrandResponse]
    total: int
    page: int
    per_page: int
