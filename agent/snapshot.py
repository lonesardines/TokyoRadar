"""Build a snapshot of agent research results for A/B comparison.

Parses the session JSONL to extract item IDs created/updated by save_items,
queries the database for full item + price_listing data, and computes metrics.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger(__name__)


def build_snapshot(session_file: str, brand_slug: str) -> dict:
    """Parse session JSONL -> extract item IDs -> query full data -> compute metrics."""
    session_path = Path(session_file)
    if not session_path.exists():
        logger.warning("Session file not found: %s", session_file)
        return _empty_snapshot()

    # 1. Parse session JSONL for tool_exec entries
    item_ids: list[int] = []
    tool_counts: dict[str, int] = {}
    scrape_results: dict[str, dict] = {}
    errors: list[str] = []
    total_tool_calls = 0

    for line in session_path.read_text().strip().split("\n"):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        if record.get("type") != "tool_exec":
            continue

        name = record.get("name", "")
        total_tool_calls += 1
        tool_counts[name] = tool_counts.get(name, 0) + 1
        output = record.get("output", "")

        if name == "save_items":
            ids = _parse_save_items_output(output)
            item_ids.extend(ids)

        elif name == "save_price_listings":
            _parse_save_listings_output(output, errors)

        elif name in ("crawl_products", "scrape_shopify_store"):
            _parse_scrape_output(name, record, scrape_results)

    # Deduplicate item IDs preserving order
    seen = set()
    unique_ids = []
    for iid in item_ids:
        if iid not in seen:
            seen.add(iid)
            unique_ids.append(iid)

    # 2. Query DB for items + price_listings
    items_data = _query_items(unique_ids) if unique_ids else []

    # 3. Compute metrics
    metrics = _compute_metrics(items_data)

    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "items": items_data,
        "metrics": metrics,
        "tool_summary": {
            "total_tool_calls": total_tool_calls,
            "tools_used": tool_counts,
            "scrape_results": scrape_results,
            "errors": errors,
        },
    }


def _empty_snapshot() -> dict:
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "items": [],
        "metrics": _compute_metrics([]),
        "tool_summary": {
            "total_tool_calls": 0,
            "tools_used": {},
            "scrape_results": {},
            "errors": [],
        },
    }


def _parse_save_items_output(output) -> list[int]:
    """Extract item IDs from save_items tool output.

    Output format: {"saved": N, "errors": [...], "items_csv": "id|name\\n101|..."}
    """
    ids: list[int] = []
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return ids

    if not isinstance(output, dict):
        return ids

    csv_text = output.get("items_csv", "")
    if not csv_text:
        return ids

    for line in csv_text.strip().split("\n")[1:]:  # skip header
        parts = line.split("|")
        if parts and parts[0].strip().isdigit():
            ids.append(int(parts[0].strip()))

    return ids


def _parse_save_listings_output(output, errors: list[str]) -> None:
    """Extract error info from save_price_listings output."""
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return

    if isinstance(output, dict):
        for err in output.get("errors", []):
            if isinstance(err, str) and err not in errors:
                errors.append(err)


def _parse_scrape_output(tool_name: str, record: dict, scrape_results: dict) -> None:
    """Extract scrape summary from crawl_products / scrape_shopify_store."""
    output = record.get("output", {})
    if isinstance(output, str):
        try:
            output = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            return

    if not isinstance(output, dict):
        return

    inp = record.get("input", {})
    if isinstance(inp, str):
        try:
            inp = json.loads(inp)
        except (json.JSONDecodeError, TypeError):
            inp = {}

    if tool_name == "crawl_products":
        url = inp.get("start_url", "") if isinstance(inp, dict) else ""
        key = _domain_from_url(url) or "unknown"
        scrape_results[key] = {
            "products_found": output.get("products_found", 0),
            "source_url": url,
        }
    elif tool_name == "scrape_shopify_store":
        domain = output.get("domain", inp.get("domain", "unknown") if isinstance(inp, dict) else "unknown")
        scrape_results[domain] = {
            "products_found": output.get("count", 0),
            "source_url": f"https://{domain}",
        }


def _domain_from_url(url: str) -> str:
    """Extract domain from URL."""
    match = re.match(r"https?://([^/]+)", url)
    return match.group(1) if match else ""


def _query_items(item_ids: list[int]) -> list[dict]:
    """Query items + price_listings from the database."""
    from tokyoradar_shared.database import SessionLocal
    from tokyoradar_shared.models import Item, PriceListing, Retailer

    items_data = []
    with SessionLocal() as db:
        items = (
            db.query(Item)
            .filter(Item.id.in_(item_ids))
            .all()
        )

        # Build a map from item_id to listings
        listing_rows = (
            db.query(PriceListing, Retailer.slug, Retailer.name)
            .join(Retailer, PriceListing.retailer_id == Retailer.id)
            .filter(PriceListing.item_id.in_(item_ids))
            .all()
        )

        listings_by_item: dict[int, list[dict]] = {}
        for pl, r_slug, r_name in listing_rows:
            listings_by_item.setdefault(pl.item_id, []).append({
                "id": pl.id,
                "retailer_slug": r_slug,
                "retailer_name": r_name,
                "price_jpy": pl.price_jpy,
                "price_usd": float(pl.price_usd) if pl.price_usd is not None else None,
                "in_stock": pl.in_stock,
                "available_sizes": pl.available_sizes,
                "url": pl.url,
                "last_checked_at": pl.last_checked_at.isoformat() if pl.last_checked_at else None,
            })

        for item in items:
            items_data.append({
                "id": item.id,
                "brand_id": item.brand_id,
                "collection_id": item.collection_id,
                "name_en": item.name_en,
                "name_ja": item.name_ja,
                "item_type": item.item_type,
                "price_jpy": item.price_jpy,
                "price_usd": float(item.price_usd) if item.price_usd is not None else None,
                "compare_at_price_usd": float(item.compare_at_price_usd) if item.compare_at_price_usd is not None else None,
                "material": item.material,
                "sizes": item.sizes,
                "primary_image_url": item.primary_image_url,
                "source_url": item.source_url,
                "external_id": item.external_id,
                "handle": item.handle,
                "vendor": item.vendor,
                "product_type_raw": item.product_type_raw,
                "tags": item.tags,
                "colors": item.colors,
                "season_code": item.season_code,
                "sku": item.sku,
                "in_stock": item.in_stock,
                "price_listings": listings_by_item.get(item.id, []),
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            })

    return items_data


def _compute_metrics(items: list[dict]) -> dict:
    """Compute aggregate metrics from snapshot items."""
    prices_usd = [
        i["price_usd"] for i in items
        if i.get("price_usd") is not None
    ]

    all_listings = []
    channels = set()
    for i in items:
        for pl in i.get("price_listings", []):
            all_listings.append(pl)
            if pl.get("retailer_slug"):
                channels.add(pl["retailer_slug"])

    return {
        "items_total": len(items),
        "items_with_images": sum(1 for i in items if i.get("primary_image_url")),
        "items_with_prices": len(prices_usd),
        "items_in_stock": sum(1 for i in items if i.get("in_stock")),
        "listings_total": len(all_listings),
        "listings_with_urls": sum(1 for pl in all_listings if pl.get("url")),
        "channels": sorted(channels),
        "channels_count": len(channels),
        "price_range_usd": [min(prices_usd), max(prices_usd)] if prices_usd else None,
        "avg_price_usd": round(sum(prices_usd) / len(prices_usd), 2) if prices_usd else None,
    }
