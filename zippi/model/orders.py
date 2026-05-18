from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    """Статусы заказа"""
    PENDING = "pending"  # Заказ создан, ожидает курьера
    PICKED_UP = "picked_up"  # Курьер забрал заказ из магазина
    DELIVERED = "delivered"  # Заказ доставлен клиенту
    CANCELLED = "cancelled"  # Заказ отменён


class OrderItem(BaseModel):
    id: int
    name: str
    quantity: int
    price: float
    total: float


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
    status: OrderStatus
    is_active: bool
    created_at: datetime
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]
    courier_id: Optional[int]
    courier_name: Optional[str] = None
    courier_phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderCard(BaseModel):
    id: int
    order_number: str
    store_address: str
    customer_address: str
    status: OrderStatus

    model_config = ConfigDict(from_attributes=True)


class PickupConfirm(BaseModel):
    order_number: str
    pickup_code: str


class DeliveryConfirm(BaseModel):
    order_number: str
    delivery_code: str


class ShiftCreate(BaseModel):
    duration_hours: int


class ShiftResponse(BaseModel):
    id: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_hours: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)