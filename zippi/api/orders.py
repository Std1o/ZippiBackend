from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from ..model.auth import User
from ..model.orders import (
    OrderResponse, OrderCard, PickupConfirm,
    DeliveryConfirm, ShiftCreate, ShiftResponse
)
from ..service.auth import get_current_user
from ..service.orders import OrderService

router = APIRouter(prefix='/orders', tags=['Заказы'])


# ========== Смены ==========
@router.post('/shift/start', response_model=ShiftResponse)
def start_shift(
    shift_data: ShiftCreate,
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Начало смены курьера"""
    return service.start_shift(user.id, shift_data)


@router.post('/shift/end', response_model=ShiftResponse)
def end_shift(
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Завершение смены курьера"""
    return service.end_shift(user.id)


@router.get('/shift/current', response_model=Optional[ShiftResponse])
def get_current_shift(
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Информация о текущей смене"""
    return service.get_current_shift(user.id)


# ========== Заказы ==========
@router.get('/available', response_model=List[OrderCard])
def get_available_orders(
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Список доступных заказов для курьеров (требуется активная смена)"""
    return service.get_available_orders(user.id)


@router.post('/take/{order_id}', response_model=OrderResponse)
async def take_order(
    order_id: int,
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Взять заказ в работу"""
    return await service.take_order(order_id, user.id)


@router.post('/confirm-pickup', response_model=OrderResponse)
async def confirm_pickup(
    data: PickupConfirm,
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Подтверждение получения заказа в магазине (по 4-значному коду)"""
    return await service.confirm_pickup(data.order_number, data.pickup_code, user.id)


@router.post('/confirm-delivery', response_model=OrderResponse)
async def confirm_delivery(
    data: DeliveryConfirm,
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Подтверждение доставки заказа клиенту (по 4-значному коду)"""
    return await service.confirm_delivery(data.order_number, data.delivery_code, user.id)


@router.get('/active', response_model=Optional[OrderResponse])
def get_active_order(
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Активный заказ курьера (который сейчас везёт)"""
    return service.get_active_order(user.id)

@router.get('/active_for_customer', response_model=Optional[OrderResponse])
def get_active_order_for_customer(
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """Активный заказ клиента"""
    return service.get_active_order_for_customer(user.id)


@router.get('/history')
def get_history(
    user: User = Depends(get_current_user),
    service: OrderService = Depends()
):
    """История доставок курьера"""
    return service.get_order_history(user.id)

@router.get('/history-courier')
def get_courier_history(
    user_id: int,
    service: OrderService = Depends()
):
    """История доставок курьера"""
    return service.get_order_history(user_id)

@router.get('/orders', response_model=List[OrderResponse])
def get_orders(
    service: OrderService = Depends()
):
    """Все заказы"""
    return service.get_orders()


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

@router.post('/admin/remove-courier/{order_number}', response_model=OrderResponse)
async def admin_remove_courier(
    order_number: str,
    service: OrderService = Depends()
):
    """Снять заказ с курьера (только для администратора)"""
    # Здесь добавьте проверку is_admin
    return await service.remove_courier_from_order(order_number)


@router.post('/admin/cancel-order/{order_number}', response_model=OrderResponse)
async def admin_cancel_order(
    order_number: str,
    service: OrderService = Depends()
):
    """Отменить заказ (только для администратора)"""
    return await service.cancel_order(order_number)


@router.post('/admin/remove-items/{order_number}', response_model=OrderResponse)
async def admin_remove_item(
    order_number: str,
    product_id: int,
    service: OrderService = Depends()
):
    """Удалить товары из заказа (только для администратора)"""
    return await service.remove_item_from_order(order_number, product_id)