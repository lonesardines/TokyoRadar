import logging
from dataclasses import dataclass, field
from decimal import Decimal

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)

# Brand-specific price bounds (USD)
PRICE_BOUNDS: dict[str, tuple[Decimal, Decimal]] = {
    "nanamica": (Decimal("30"), Decimal("2000")),
}

DEFAULT_PRICE_BOUNDS = (Decimal("5"), Decimal("5000"))

KNOWN_PRODUCT_TYPES = {
    "jacket", "coat", "shirt", "t-shirt", "pants", "trousers", "shorts",
    "sweater", "hoodie", "vest", "bag", "hat", "cap", "accessory", "socks",
    "scarf", "belt", "shoes", "sneakers", "polo", "cardigan", "parka",
    "blazer", "overshirt", "down jacket", "fleece", "bottom", "dress",
    "skirt", "footwear", "knit", "sweat", "top", "outerwear",
}


@dataclass
class ValidationFlag:
    field: str
    severity: str  # "warning" or "error"
    message: str


@dataclass
class ValidatedProduct:
    raw_index: int
    external_id: str
    name: str
    is_valid: bool = True
    flags: list[ValidationFlag] = field(default_factory=list)
    data: dict = field(default_factory=dict)


class ProductValidator(BaseModel):
    external_id: str
    name: str
    price_usd: Decimal | None = None
    primary_image_url: str | None = None
    product_type: str | None = None
    handle: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Product name is empty")
        return v


def validate_products(
    raw_products: list[dict],
    brand_slug: str,
) -> list[ValidatedProduct]:
    """Validate a list of raw product dicts, returning validated results with flags."""
    min_price, max_price = PRICE_BOUNDS.get(brand_slug, DEFAULT_PRICE_BOUNDS)
    results: list[ValidatedProduct] = []

    for i, raw in enumerate(raw_products):
        vp = ValidatedProduct(
            raw_index=i,
            external_id=raw.get("external_id", ""),
            name=raw.get("name", ""),
            data=raw,
        )

        # Required fields
        if not vp.external_id:
            vp.flags.append(ValidationFlag("external_id", "error", "Missing external_id"))
            vp.is_valid = False

        if not vp.name:
            vp.flags.append(ValidationFlag("name", "error", "Missing product name"))
            vp.is_valid = False

        # Price bounds
        price = raw.get("price_usd")
        if price is not None:
            price_dec = Decimal(str(price))
            if price_dec < min_price:
                vp.flags.append(ValidationFlag(
                    "price_usd", "warning",
                    f"Price ${price_dec} below minimum ${min_price}",
                ))
            elif price_dec > max_price:
                vp.flags.append(ValidationFlag(
                    "price_usd", "warning",
                    f"Price ${price_dec} above maximum ${max_price}",
                ))
        else:
            vp.flags.append(ValidationFlag("price_usd", "warning", "No price available"))

        # Image check
        if not raw.get("primary_image_url"):
            vp.flags.append(ValidationFlag(
                "primary_image_url", "warning", "No primary image",
            ))

        # Product type check
        product_type = (raw.get("product_type") or "").lower().strip()
        if product_type and product_type not in KNOWN_PRODUCT_TYPES:
            vp.flags.append(ValidationFlag(
                "product_type", "warning",
                f"Unknown product type: '{product_type}'",
            ))

        results.append(vp)

    valid_count = sum(1 for r in results if r.is_valid)
    flagged_count = sum(1 for r in results if r.flags)
    logger.info(
        "Validation: %d/%d valid, %d flagged for brand '%s'",
        valid_count, len(results), flagged_count, brand_slug,
    )
    return results
