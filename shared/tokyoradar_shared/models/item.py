from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from tokyoradar_shared.database import Base


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_brand_external", "brand_id", "external_id", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id"), nullable=False)
    collection_id: Mapped[int | None] = mapped_column(
        ForeignKey("collections.id"), nullable=True
    )
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ja: Mapped[str | None] = mapped_column(String(255), nullable=True)
    item_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    price_jpy: Mapped[int | None] = mapped_column(nullable=True)
    price_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    material: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sizes: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    primary_image_url: Mapped[str | None] = mapped_column(
        String(1024), nullable=True
    )
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )

    # Phase 2 columns
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    handle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    product_type_raw: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    colors: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    body_html_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    season_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    in_stock: Mapped[bool | None] = mapped_column(nullable=True, default=True)
    compare_at_price_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    shopify_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=func.now(), nullable=True
    )
