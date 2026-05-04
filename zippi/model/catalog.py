from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    old_price: Optional[float] = None
    image_url: Optional[str] = None
    category_id: int
    stock: int = 0


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ProductWithCategory(ProductResponse):
    category_name: str