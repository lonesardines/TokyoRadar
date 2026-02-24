from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Brand, Item
from app.schemas.item import ItemDetailResponse, ItemListResponse, ItemResponse

router = APIRouter()


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

    return ItemListResponse(
        data=[ItemResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{item_id}", response_model=ItemDetailResponse)
def get_item(item_id: int, db: Session = Depends(get_db)) -> ItemDetailResponse:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemDetailResponse.model_validate(item)
