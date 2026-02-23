from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.brand import Brand
from app.schemas.brand import (
    BrandCreate,
    BrandListResponse,
    BrandResponse,
    BrandUpdate,
)

router = APIRouter()


@router.get("", response_model=BrandListResponse)
def list_brands(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    style_tag: str | None = None,
    price_range: str | None = None,
    shipping_tier: str | None = None,
    sort_by: str = Query("name_en", pattern="^(name_en|created_at|founded_year)$"),
    db: Session = Depends(get_db),
) -> BrandListResponse:
    query = db.query(Brand)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Brand.name_en.ilike(search_filter),
                Brand.name_ja.ilike(search_filter),
                Brand.designer.ilike(search_filter),
            )
        )

    if style_tag:
        query = query.filter(Brand.style_tags.any(style_tag))

    if price_range:
        query = query.filter(Brand.price_range == price_range)

    if shipping_tier:
        query = query.filter(Brand.shipping_tier == shipping_tier)

    total = query.count()

    sort_column = getattr(Brand, sort_by, Brand.name_en)
    query = query.order_by(sort_column)

    brands = query.offset((page - 1) * per_page).limit(per_page).all()

    return BrandListResponse(
        data=[BrandResponse.model_validate(b) for b in brands],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{slug}", response_model=BrandResponse)
def get_brand(slug: str, db: Session = Depends(get_db)) -> BrandResponse:
    brand = db.query(Brand).filter(Brand.slug == slug).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    return BrandResponse.model_validate(brand)


@router.post("", response_model=BrandResponse, status_code=201)
def create_brand(
    brand_in: BrandCreate, db: Session = Depends(get_db)
) -> BrandResponse:
    brand = Brand(**brand_in.model_dump())
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return BrandResponse.model_validate(brand)


@router.put("/{slug}", response_model=BrandResponse)
def update_brand(
    slug: str, brand_in: BrandUpdate, db: Session = Depends(get_db)
) -> BrandResponse:
    brand = db.query(Brand).filter(Brand.slug == slug).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")

    update_data = brand_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(brand, field, value)

    db.commit()
    db.refresh(brand)
    return BrandResponse.model_validate(brand)


@router.delete("/{slug}", status_code=204)
def delete_brand(slug: str, db: Session = Depends(get_db)) -> None:
    brand = db.query(Brand).filter(Brand.slug == slug).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    db.delete(brand)
    db.commit()
