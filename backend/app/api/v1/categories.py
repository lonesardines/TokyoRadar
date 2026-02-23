from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)

router = APIRouter()


def _build_tree(categories: list[Category]) -> list[CategoryResponse]:
    by_id: dict[int, CategoryResponse] = {}
    roots: list[CategoryResponse] = []

    for cat in categories:
        node = CategoryResponse(
            id=cat.id,
            name=cat.name,
            slug=cat.slug,
            description=cat.description,
            parent_id=cat.parent_id,
            sort_order=cat.sort_order,
            children=[],
        )
        by_id[cat.id] = node

    for cat in categories:
        node = by_id[cat.id]
        if cat.parent_id and cat.parent_id in by_id:
            parent = by_id[cat.parent_id]
            if parent.children is None:
                parent.children = []
            parent.children.append(node)
        else:
            roots.append(node)

    return roots


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    tree: bool = Query(False),
    db: Session = Depends(get_db),
) -> list[CategoryResponse]:
    categories = db.query(Category).order_by(Category.sort_order).all()

    if tree:
        return _build_tree(categories)

    return [CategoryResponse.model_validate(c) for c in categories]


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(
    cat_in: CategoryCreate, db: Session = Depends(get_db)
) -> CategoryResponse:
    category = Category(**cat_in.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return CategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, cat_in: CategoryUpdate, db: Session = Depends(get_db)
) -> CategoryResponse:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    update_data = cat_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)) -> None:
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
