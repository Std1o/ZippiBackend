from fastapi import APIRouter, Depends, HTTPException

from ..model.auth import User
from ..model.cart import (
    CartItemCreate, CartResponse, CheckoutRequest
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


@router.delete('/item/{product_id}', response_model=CartResponse)
def remove_cart_item(
    product_id: int,
    user: User = Depends(get_current_user),
    service: CartService = Depends()
):
    """
    Удаление или уменьшение количества товара из корзины.
    Уменьшает количество на 1. Если количество становится 0, товар удаляется.
    """
    return service.remove_cart_item(user.id, product_id)


@router.delete('/clear')
def clear_cart(
    user: User = Depends(get_current_user),
    service: CartService = Depends()
):
    """Полная очистка корзины"""
    service.clear_cart(user.id)
    return {"message": "Корзина очищена"}


@router.post('/checkout')
def checkout(
    checkout_data: CheckoutRequest,
    user: User = Depends(get_current_user),
    service: CartService = Depends()
):
    """Оформление заказа из корзины"""
    return service.checkout(user.id, checkout_data)