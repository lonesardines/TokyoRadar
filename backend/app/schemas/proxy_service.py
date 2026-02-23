from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProxyServiceBase(BaseModel):
    slug: str
    name: str
    website: str | None = None
    service_type: str | None = None
    fee_structure: dict | None = None
    supported_retailers: list[str] | None = None
    shipping_methods: list[str] | None = None
    avg_delivery_days_us: int | None = None
    pros: list[str] | None = None
    cons: list[str] | None = None
    description_en: str | None = None
    logo_url: str | None = None


class ProxyServiceCreate(ProxyServiceBase):
    pass


class ProxyServiceUpdate(BaseModel):
    slug: str | None = None
    name: str | None = None
    website: str | None = None
    service_type: str | None = None
    fee_structure: dict | None = None
    supported_retailers: list[str] | None = None
    shipping_methods: list[str] | None = None
    avg_delivery_days_us: int | None = None
    pros: list[str] | None = None
    cons: list[str] | None = None
    description_en: str | None = None
    logo_url: str | None = None


class ProxyServiceResponse(ProxyServiceBase):
    id: int
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
