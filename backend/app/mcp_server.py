"""Backend DB MCP Server — exposes database query tools via MCP."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings
from sqlalchemy import select

from tokyoradar_shared.database import SessionLocal
from tokyoradar_shared.models import Brand, Item, PriceListing, Retailer

mcp = FastMCP(
    "TokyoRadar DB",
    streamable_http_path="/",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


@mcp.tool()
def get_brand_info(brand_slug: str) -> dict:
    """Get brand metadata, buy_guide channels, and valid retailer slugs.
    Use this FIRST to understand the brand before scraping.
    Returns valid_retailer_slugs — use ONLY these for save_price_listings.
    For any Japanese official store, use retailer_slug='brand-official-jp'."""
    with SessionLocal() as db:
        brand = db.execute(
            select(Brand).where(Brand.slug == brand_slug)
        ).scalar_one_or_none()

        if brand is None:
            return {"error": f"Brand '{brand_slug}' not found"}

        # Include valid retailer slugs so the agent always has them
        retailers = db.execute(
            select(Retailer.slug, Retailer.name).order_by(Retailer.name)
        ).all()
        retailer_slug_map = {r.name: r.slug for r in retailers}

        return {
            "id": brand.id,
            "slug": brand.slug,
            "name_en": brand.name_en,
            "name_ja": brand.name_ja,
            "website_jp": brand.website_jp,
            "website_us": brand.website_us,
            "shipping_tier": brand.shipping_tier,
            "price_range": brand.price_range,
            "buy_guide": brand.buy_guide,
            "valid_retailer_slugs": retailer_slug_map,
        }


@mcp.tool()
def search_items_db(
    brand_slug: str,
    name_query: str | None = None,
    limit: int = 200,
) -> dict:
    """Search existing items in the DB for a brand. Returns compact CSV: id|name|sku|price_usd.
    Use this to find item IDs needed for save_price_listings.
    Call in PARALLEL with get_brand_info and list_retailers."""
    with SessionLocal() as db:
        brand = db.execute(
            select(Brand).where(Brand.slug == brand_slug)
        ).scalar_one_or_none()

        if brand is None:
            return {"error": f"Brand '{brand_slug}' not found"}

        query = select(Item).where(Item.brand_id == brand.id)
        if name_query:
            query = query.where(Item.name_en.ilike(f"%{name_query}%"))
        query = query.limit(limit)

        items = db.execute(query).scalars().all()

        fields = ["id", "name", "sku", "price_usd"]
        lines = ["|".join(fields)]
        for item in items:
            lines.append("|".join([
                str(item.id),
                item.name_en or "",
                item.sku or "",
                str(item.price_usd) if item.price_usd else "",
            ]))

        return {
            "brand_slug": brand_slug,
            "count": len(items),
            "items_csv": "\n".join(lines),
        }


@mcp.tool()
def save_price_listings(listings: list[dict]) -> dict:
    """Save price listings to DB. Each listing MUST include:
    - item_id (int): from save_items or search_items_db
    - retailer_slug (str): from list_retailers or valid_retailer_slugs
    - price_usd or price_jpy: the price at this retailer
    - url (str): direct link to the product page at this retailer (from product_url in crawl output)
    Do NOT call until you have item IDs from save_items."""
    saved = 0
    errors = []

    with SessionLocal() as db:
        for listing_data in listings:
            try:
                retailer = db.execute(
                    select(Retailer).where(
                        Retailer.slug == listing_data["retailer_slug"]
                    )
                ).scalar_one_or_none()

                if retailer is None:
                    all_slugs = [r.slug for r in db.execute(select(Retailer.slug)).scalars().all()]
                    errors.append(
                        f"Retailer '{listing_data['retailer_slug']}' not found. "
                        f"Valid slugs: {', '.join(sorted(all_slugs))}"
                    )
                    continue

                item = db.execute(
                    select(Item).where(Item.id == listing_data["item_id"])
                ).scalar_one_or_none()

                if item is None:
                    errors.append(f"Item ID {listing_data['item_id']} not found")
                    continue

                existing = db.execute(
                    select(PriceListing).where(
                        PriceListing.item_id == listing_data["item_id"],
                        PriceListing.retailer_id == retailer.id,
                    )
                ).scalar_one_or_none()

                if existing:
                    if listing_data.get("price_usd") is not None:
                        existing.price_usd = Decimal(str(listing_data["price_usd"]))
                    if listing_data.get("price_jpy") is not None:
                        existing.price_jpy = listing_data["price_jpy"]
                    if "in_stock" in listing_data:
                        existing.in_stock = listing_data["in_stock"]
                    if listing_data.get("url"):
                        existing.url = listing_data["url"]
                    existing.last_checked_at = datetime.now()
                else:
                    pl = PriceListing(
                        item_id=listing_data["item_id"],
                        retailer_id=retailer.id,
                        price_usd=Decimal(str(listing_data["price_usd"])) if listing_data.get("price_usd") else None,
                        price_jpy=listing_data.get("price_jpy"),
                        in_stock=listing_data.get("in_stock", True),
                        url=listing_data.get("url"),
                        last_checked_at=datetime.now(),
                    )
                    db.add(pl)

                saved += 1

            except Exception as exc:
                errors.append(f"Error: {exc}")

        db.commit()

    return {"saved": saved, "errors": errors}


@mcp.tool()
def save_items(brand_slug: str, items: list[dict]) -> dict:
    """Upsert Item records for a brand. Creates new items or updates existing ones.
    Match by external_id (if provided) or name+brand_id.
    Input items: [{name, sku?, price_usd?, price_jpy?, external_id?, source_url?, material?, sizes?, in_stock?, primary_image_url?}]
    Returns {saved: N, errors: [], items_csv: "id|name\\n..."} — use item IDs for save_price_listings."""
    saved = 0
    errors = []
    result_items = []

    with SessionLocal() as db:
        brand = db.execute(
            select(Brand).where(Brand.slug == brand_slug)
        ).scalar_one_or_none()

        if brand is None:
            return {"error": f"Brand '{brand_slug}' not found"}

        for item_data in items:
            try:
                name = item_data.get("name", "").strip()
                if not name:
                    errors.append("Skipped item with empty name")
                    continue

                external_id = item_data.get("external_id")

                # Try to find existing item
                existing = None
                if external_id:
                    existing = db.execute(
                        select(Item).where(
                            Item.brand_id == brand.id,
                            Item.external_id == str(external_id),
                        )
                    ).scalar_one_or_none()

                if existing is None:
                    existing = db.execute(
                        select(Item).where(
                            Item.brand_id == brand.id,
                            Item.name_en == name,
                        )
                    ).scalar_one_or_none()

                if existing:
                    # Update existing item
                    if item_data.get("sku"):
                        existing.sku = item_data["sku"]
                    if item_data.get("price_usd") is not None:
                        existing.price_usd = Decimal(str(item_data["price_usd"]))
                    if item_data.get("price_jpy") is not None:
                        existing.price_jpy = item_data["price_jpy"]
                    if item_data.get("source_url"):
                        existing.source_url = item_data["source_url"]
                    if item_data.get("material"):
                        existing.material = item_data["material"]
                    if item_data.get("sizes"):
                        existing.sizes = item_data["sizes"]
                    if "in_stock" in item_data:
                        existing.in_stock = item_data["in_stock"]
                    if item_data.get("primary_image_url"):
                        existing.primary_image_url = item_data["primary_image_url"]
                    if external_id and not existing.external_id:
                        existing.external_id = str(external_id)
                    result_items.append((existing.id, existing.name_en))
                else:
                    # Create new item
                    new_item = Item(
                        brand_id=brand.id,
                        name_en=name,
                        sku=item_data.get("sku"),
                        price_usd=Decimal(str(item_data["price_usd"])) if item_data.get("price_usd") else None,
                        price_jpy=item_data.get("price_jpy"),
                        external_id=str(external_id) if external_id else None,
                        source_url=item_data.get("source_url"),
                        material=item_data.get("material"),
                        sizes=item_data.get("sizes"),
                        in_stock=item_data.get("in_stock", True),
                        primary_image_url=item_data.get("primary_image_url"),
                    )
                    db.add(new_item)
                    db.flush()  # Get the ID
                    result_items.append((new_item.id, new_item.name_en))

                saved += 1
            except Exception as exc:
                errors.append(f"Error saving '{item_data.get('name', '?')}': {exc}")

        db.commit()

    # Build CSV of saved items
    lines = ["id|name"]
    for item_id, item_name in result_items:
        lines.append(f"{item_id}|{item_name}")

    return {
        "saved": saved,
        "errors": errors,
        "items_csv": "\n".join(lines),
    }


@mcp.tool()
def list_retailers() -> dict:
    """List all retailers in the DB with their slug, name, website, and shipping tier.
    Returns compact CSV: slug|name|website|shipping_tier.
    Use this to map buy_guide channel names to retailer slugs for save_price_listings."""
    with SessionLocal() as db:
        retailers = db.execute(
            select(Retailer).order_by(Retailer.name)
        ).scalars().all()

        lines = ["slug|name|website|shipping_tier"]
        for r in retailers:
            lines.append("|".join([
                r.slug,
                r.name,
                r.website or "",
                r.shipping_tier or "",
            ]))

        return {
            "count": len(retailers),
            "retailers_csv": "\n".join(lines),
        }
