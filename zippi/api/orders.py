from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from ..model.auth import User
from ..model.orders import OrderResponse, OrderCard, PickupConfirm, DeliveryConfirm
from ..service.auth import get_current_user
from ..service.orders import OrderService

router = APIRouter(prefix='/orders', tags=['Заказы'])


@router.get('/available', response_model=List[OrderCard])
def get_available_orders(
    service: OrderService = Depends()
):
    """Список доступных заказов для курьеров"""
    return service.get_available_orders()


@router.post('/take/{order_id}', response_model=OrderResponse)
def take_order(
    order_id: int,
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Взять заказ в работу (только для курьеров)"""
    return service.take_order(order_id, user.id)


@router.post('/confirm-pickup', response_model=OrderResponse)
def confirm_pickup(
    data: PickupConfirm,
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Подтверждение получения заказа в магазине (по 4-значному коду)"""
    return service.confirm_pickup(data.order_number, data.pickup_code, user.id)


@router.post('/confirm-delivery', response_model=OrderResponse)
def confirm_delivery(
    data: DeliveryConfirm,
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Подтверждение доставки заказа клиенту (по 4-значному коду)"""
    return service.confirm_delivery(data.order_number, data.delivery_code, user.id)


@router.put('/status/{order_number}', response_model=OrderResponse)
def update_order_status(
    order_number: str,
    status: str,
    service: OrderService = Depends()
):
    """Обновление статуса заказа (для магазина/админа)"""
    return service.update_order_status(order_number, status)


@router.get('/active', response_model=Optional[OrderResponse])
def get_active_order(
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Активный заказ курьера (который сейчас везёт)"""
    return service.get_active_order(user.id)


@router.get('/history')
def get_history(
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """История доставок курьера"""
    return service.get_order_history(user.id)


@router.get('/my-orders', response_model=List[OrderResponse])
def get_my_orders(
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Все заказы курьера"""
    return service.get_my_orders(user.id)


@router.get('/my-purchases', response_model=List[OrderResponse])
def get_my_purchases(
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Мои заказы как клиента"""
    return service.get_my_orders_as_customer(user.id)


@router.get('/{order_number}', response_model=OrderResponse)
def get_order(
    order_number: str,
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Детальная информация о заказе"""
    order = service.get_order_by_number(order_number)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    return order