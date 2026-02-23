from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceListing(Base):
    __tablename__ = "price_listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    retailer_id: Mapped[int] = mapped_column(
        ForeignKey("retailers.id"), nullable=False
    )
    price_jpy: Mapped[int | None] = mapped_column(nullable=True)
    price_usd: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    in_stock: Mapped[bool] = mapped_column(default=True)
    available_sizes: Mapped[list[str] | None] = mapped_column(
        ARRAY(String), nullable=True
    )
    url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
    )
