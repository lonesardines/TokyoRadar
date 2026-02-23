from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CategoryBase(BaseModel):
    name: str
    slug: str
    description: str | None = None
    parent_id: int | None = None
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    parent_id: int | None = None
    sort_order: int | None = None


class CategoryResponse(CategoryBase):
    id: int
    children: list[CategoryResponse] | None = None

    model_config = ConfigDict(from_attributes=True)
