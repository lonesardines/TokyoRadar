from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.proxy_service import ProxyService
from app.schemas.common import PaginatedResponse
from app.schemas.proxy_service import (
    ProxyServiceCreate,
    ProxyServiceResponse,
    ProxyServiceUpdate,
)

router = APIRouter()


@router.get("", response_model=PaginatedResponse[ProxyServiceResponse])
def list_proxy_services(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    service_type: str | None = None,
    db: Session = Depends(get_db),
) -> PaginatedResponse[ProxyServiceResponse]:
    query = db.query(ProxyService)

    if service_type:
        query = query.filter(ProxyService.service_type == service_type)

    total = query.count()
    services = (
        query.order_by(ProxyService.name)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return PaginatedResponse(
        data=[ProxyServiceResponse.model_validate(s) for s in services],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{slug}", response_model=ProxyServiceResponse)
def get_proxy_service(
    slug: str, db: Session = Depends(get_db)
) -> ProxyServiceResponse:
    service = db.query(ProxyService).filter(ProxyService.slug == slug).first()
    if not service:
        raise HTTPException(status_code=404, detail="Proxy service not found")
    return ProxyServiceResponse.model_validate(service)


@router.post("", response_model=ProxyServiceResponse, status_code=201)
def create_proxy_service(
    service_in: ProxyServiceCreate, db: Session = Depends(get_db)
) -> ProxyServiceResponse:
    service = ProxyService(**service_in.model_dump())
    db.add(service)
    db.commit()
    db.refresh(service)
    return ProxyServiceResponse.model_validate(service)


@router.put("/{slug}", response_model=ProxyServiceResponse)
def update_proxy_service(
    slug: str, service_in: ProxyServiceUpdate, db: Session = Depends(get_db)
) -> ProxyServiceResponse:
    service = db.query(ProxyService).filter(ProxyService.slug == slug).first()
    if not service:
        raise HTTPException(status_code=404, detail="Proxy service not found")

    update_data = service_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)
    return ProxyServiceResponse.model_validate(service)


@router.delete("/{slug}", status_code=204)
def delete_proxy_service(slug: str, db: Session = Depends(get_db)) -> None:
    service = db.query(ProxyService).filter(ProxyService.slug == slug).first()
    if not service:
        raise HTTPException(status_code=404, detail="Proxy service not found")
    db.delete(service)
    db.commit()
