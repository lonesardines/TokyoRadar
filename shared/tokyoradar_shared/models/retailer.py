from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from tokyoradar_shared.database import Base


class Retailer(Base):
    __tablename__ = "retailers"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ships_to_us: Mapped[bool] = mapped_column(default=False)
    shipping_tier: Mapped[str | None] = mapped_column(String(50), nullable=True)
    supported_proxies: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    payment_methods: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=func.now(), nullable=True
    )
