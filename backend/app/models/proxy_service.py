from datetime import datetime

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProxyService(Base):
    __tablename__ = "proxy_services"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    service_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fee_structure: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    supported_retailers: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    shipping_methods: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    avg_delivery_days_us: Mapped[int | None] = mapped_column(nullable=True)
    pros: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    cons: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        onupdate=func.now(), nullable=True
    )
