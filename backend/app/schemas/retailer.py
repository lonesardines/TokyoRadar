from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RetailerBase(BaseModel):
    slug: str
    name: str
    website: str | None = None
    country: str | None = None
    ships_to_us: bool = False
    shipping_tier: str | None = None
    supported_proxies: list[str] | None = None
    payment_methods: list[str] | None = None
    description_en: str | None = None
    logo_url: str | None = None


class RetailerCreate(RetailerBase):
    pass


class RetailerUpdate(BaseModel):
    slug: str | None = None
    name: str | None = None
    website: str | None = None
    country: str | None = None
    ships_to_us: bool | None = None
    shipping_tier: str | None = None
    supported_proxies: list[str] | None = None
    payment_methods: list[str] | None = None
    description_en: str | None = None
    logo_url: str | None = None


class RetailerResponse(RetailerBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
