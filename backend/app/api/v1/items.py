from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Brand, Item, PriceListing, Retailer
from app.schemas.item import (
    ItemDetailResponse,
    ItemListResponse,
    ItemResponse,
    PriceListingResponse,
)

router = APIRouter()


def _attach_price_listings(
    items: list[Item], db: Session
) -> list[dict]:
    """Load price listings for a batch of items and build response dicts."""
    if not items:
        return []

    item_ids = [i.id for i in items]

    rows = (
        db.query(PriceListing, Retailer.slug, Retailer.name)
        .join(Retailer, PriceListing.retailer_id == Retailer.id)
        .filter(PriceListing.item_id.in_(item_ids))
        .all()
    )

    # Group by item_id
    listings_by_item: dict[int, list[PriceListingResponse]] = {}
    for pl, retailer_slug, retailer_name in rows:
        resp = PriceListingResponse(
            id=pl.id,
            retailer_slug=retailer_slug,
            retailer_name=retailer_name,
            price_jpy=pl.price_jpy,
            price_usd=pl.price_usd,
            in_stock=pl.in_stock,
            available_sizes=pl.available_sizes,
            url=pl.url,
            last_checked_at=pl.last_checked_at,
        )
        listings_by_item.setdefault(pl.item_id, []).append(resp)

    results = []
    for item in items:
        item_dict = ItemResponse.model_validate(item).model_dump()
        item_dict["price_listings"] = listings_by_item.get(item.id, [])
        results.append(item_dict)
    return results


@router.get("", response_model=ItemListResponse)
def list_items(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    brand_slug: str | None = None,
    search: str | None = None,
    item_type: str | None = None,
    season_code: str | None = None,
    in_stock: bool | None = None,
    db: Session = Depends(get_db),
) -> ItemListResponse:
    query = db.query(Item)

    if brand_slug:
        brand = db.query(Brand).filter(Brand.slug == brand_slug).first()
        if brand:
            query = query.filter(Item.brand_id == brand.id)
        else:
            return ItemListResponse(data=[], total=0, page=page, per_page=per_page)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Item.name_en.ilike(search_filter),
                Item.name_ja.ilike(search_filter),
                Item.sku.ilike(search_filter),
            )
        )

    if item_type:
        query = query.filter(Item.item_type == item_type)

    if season_code:
        query = query.filter(Item.season_code == season_code)

    if in_stock is not None:
        query = query.filter(Item.in_stock == in_stock)

    total = query.count()
    items = query.order_by(Item.created_at.desc()).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    items_with_listings = _attach_price_listings(items, db)

    return ItemListResponse(
        data=items_with_listings,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{item_id}", response_model=ItemDetailResponse)
def get_item(item_id: int, db: Session = Depends(get_db)) -> ItemDetailResponse:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Attach price listings
    rows = (
        db.query(PriceListing, Retailer.slug, Retailer.name)
        .join(Retailer, PriceListing.retailer_id == Retailer.id)
        .filter(PriceListing.item_id == item_id)
        .all()
    )
    listings = [
        PriceListingResponse(
            id=pl.id,
            retailer_slug=retailer_slug,
            retailer_name=retailer_name,
            price_jpy=pl.price_jpy,
            price_usd=pl.price_usd,
            in_stock=pl.in_stock,
            available_sizes=pl.available_sizes,
            url=pl.url,
            last_checked_at=pl.last_checked_at,
        )
        for pl, retailer_slug, retailer_name in rows
    ]

    item_dict = ItemDetailResponse.model_validate(item).model_dump()
    item_dict["price_listings"] = listings
    return item_dict
