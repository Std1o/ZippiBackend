from fastapi import APIRouter, Depends

from ..model.auth import User
from ..model.cart import (
    CartItemCreate, CartResponse, CartUpdate,
    CheckoutRequest, CheckoutResponse
)
from ..service.auth import get_current_user
from ..service.cart import CartService

router = APIRouter(prefix='/cart', tags=['Корзина'])


@router.get('/', response_model=CartResponse)
def get_cart(
    user: User = Depends(get_current_user),
    service: CartService = Depends()
):
    """Получение корзины пользователя"""
    return service.get_cart(user.id)


@router.post('/add', response_model=CartResponse)
def add_to_cart(
    item: CartItemCreate,
    user: User = Depends(get_current_user),
    service: CartService = Depends()
):
    """Добавление товара в корзину"""
    return service.add_to_cart(user.id, item)


@router.put('/item/{item_id}', response_model=CartResponse)
def update_cart_item(
    item_id: int,
    update_data: CartUpdate,
    user: User = Depends(get_current_user),
    service: CartService = Depends()
):
    """Обновление количества товара в корзине"""
    return service.update_cart_item(user.id, item_id, update_data)


@router.delete('/item/{item_id}', response_model=CartResponse)
def remove_from_cart(
    item_id: int,
    user: User = Depends(get_current_user),
    service: CartService = Depends()
):
    """Удаление товара из корзины"""
    return service.remove_from_cart(user.id, item_id)


@router.delete('/clear')
def clear_cart(
    user: User = Depends(get_current_user),
    service: CartService = Depends()
):
    """Очистка корзины"""
    service.clear_cart(user.id)
    return {"message": "Корзина очищена"}


@router.post('/checkout', response_model=CheckoutResponse)
def checkout(
    checkout_data: CheckoutRequest,
    user: User = Depends(get_current_user),
    service: CartService = Depends()
):
    """Оформление заказа из корзины"""
    return service.checkout(user.id, checkout_data)