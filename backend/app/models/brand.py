from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name_en: Mapped[str] = mapped_column(String(255), nullable=False)
    name_ja: Mapped[str | None] = mapped_column(String(255), nullable=True)
    designer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(nullable=True)
    headquarters: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_jp: Mapped[str | None] = mapped_column(String(512), nullable=True)
    website_us: Mapped[str | None] = mapped_column(String(512), nullable=True)
    has_redirect: Mapped[bool] = mapped_column(default=False)
    style_tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    price_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ja: Mapped[str | None] = mapped_column(Text, nullable=True)
    shipping_tier: Mapped[str | None] = mapped_column(String(50), nullable=True)
    buy_guide: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=func.now(), nullable=True
    )
