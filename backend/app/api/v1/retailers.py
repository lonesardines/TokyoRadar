from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.retailer import Retailer
from app.schemas.common import PaginatedResponse
from app.schemas.retailer import (
    RetailerCreate,
    RetailerResponse,
    RetailerUpdate,
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[RetailerResponse])
def list_retailers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    shipping_tier: str | None = None,
    db: Session = Depends(get_db),
) -> PaginatedResponse[RetailerResponse]:
    query = db.query(Retailer)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                Retailer.name.ilike(search_filter),
                Retailer.description_en.ilike(search_filter),
            )
        )

    if shipping_tier:
        query = query.filter(Retailer.shipping_tier == shipping_tier)

    total = query.count()
    retailers = (
        query.order_by(Retailer.name)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedResponse(
        data=[RetailerResponse.model_validate(r) for r in retailers],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{slug}", response_model=RetailerResponse)
def get_retailer(slug: str, db: Session = Depends(get_db)) -> RetailerResponse:
    retailer = db.query(Retailer).filter(Retailer.slug == slug).first()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")
    return RetailerResponse.model_validate(retailer)


@router.post("", response_model=RetailerResponse, status_code=201)
def create_retailer(
    retailer_in: RetailerCreate, db: Session = Depends(get_db)
) -> RetailerResponse:
    retailer = Retailer(**retailer_in.model_dump())
    db.add(retailer)
    db.commit()
    db.refresh(retailer)
    return RetailerResponse.model_validate(retailer)


@router.put("/{slug}", response_model=RetailerResponse)
def update_retailer(
    slug: str, retailer_in: RetailerUpdate, db: Session = Depends(get_db)
) -> RetailerResponse:
    retailer = db.query(Retailer).filter(Retailer.slug == slug).first()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")

    update_data = retailer_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(retailer, field, value)

    db.commit()
    db.refresh(retailer)
    return RetailerResponse.model_validate(retailer)


@router.delete("/{slug}", status_code=204)
def delete_retailer(slug: str, db: Session = Depends(get_db)) -> None:
    retailer = db.query(Retailer).filter(Retailer.slug == slug).first()
    if not retailer:
        raise HTTPException(status_code=404, detail="Retailer not found")
    db.delete(retailer)
    db.commit()
