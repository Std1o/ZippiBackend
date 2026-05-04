from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class CartItemBase(BaseModel):
    product_id: int
    quantity: int


class CartItemCreate(CartItemBase):
    pass


class CartItemResponse(CartItemBase):
    id: int
    product_name: str
    product_price: float
    product_image: Optional[str]
    total_price: float

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    id: int
    items: List[CartItemResponse]
    total_quantity: int
    total_amount: float
    updated_at: datetime


class CartUpdate(BaseModel):
    quantity: int


class CheckoutRequest(BaseModel):
    customer_name: str
    customer_phone: str
    customer_address: str
    customer_latitude: Optional[float] = None
    customer_longitude: Optional[float] = None


class CheckoutResponse(BaseModel):
    order: dict
    message: str