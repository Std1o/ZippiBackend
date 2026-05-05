from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class OrderItem(BaseModel):
    id: int
    name: str
    quantity: int
    price: float
    total: float


class OrderCreate(BaseModel):
    store_address: str
    customer_address: str
    customer_phone: str
    customer_name: str
    items: List[dict]
    total_amount: float
    store_latitude: Optional[float] = None
    store_longitude: Optional[float] = None
    customer_latitude: Optional[float] = None
    customer_longitude: Optional[float] = None


class OrderResponse(BaseModel):
    id: int
    order_number: str
    pickup_code: str
    delivery_code: str
    store_address: str
    customer_address: str
    customer_phone: str
    customer_name: str
    items: List[dict]
    total_amount: float
    status: str
    is_active: bool
    created_at: datetime
    ready_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]
    courier_id: Optional[int]

    class Config:
        from_attributes = True


class OrderCard(BaseModel):
    id: int
    order_number: str
    store_address: str
    customer_address: str
    status: str
    distance: Optional[float] = None


class PickupConfirm(BaseModel):
    order_number: str
    pickup_code: str


class DeliveryConfirm(BaseModel):
    order_number: str
    delivery_code: str