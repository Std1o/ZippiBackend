import json
from datetime import datetime
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..model.cart import (
    CartItemCreate, CartItemResponse, CartResponse,
    CartUpdate, CheckoutRequest, CheckoutResponse
)
from ..service.orders import OrderService
from .. import tables


class CartService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def _get_or_create_cart(self, user_id: int) -> tables.Cart:
        """Получение или создание корзины пользователя"""
        cart = self.session.query(tables.Cart).filter_by(user_id=user_id).first()
        if not cart:
            cart = tables.Cart(user_id=user_id)
            self.session.add(cart)
            self.session.commit()
            self.session.refresh(cart)
        return cart

    def _to_cart_response(self, cart: tables.Cart) -> CartResponse:
        """Преобразование корзины в ответ API"""
        items = []
        total_quantity = 0
        total_amount = 0

        for item in cart.items:
            product = item.product
            total_price = product.price * item.quantity
            items.append(CartItemResponse(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                product_name=product.name,
                product_price=product.price,
                product_image=product.image_url,
                total_price=total_price
            ))
            total_quantity += item.quantity
            total_amount += total_price

        return CartResponse(
            id=cart.id,
            items=items,
            total_quantity=total_quantity,
            total_amount=total_amount,
            updated_at=cart.updated_at
        )

    def get_cart(self, user_id: int) -> CartResponse:
        """Получение корзины пользователя"""
        cart = self._get_or_create_cart(user_id)
        return self._to_cart_response(cart)

    def add_to_cart(self, user_id: int, item_data: CartItemCreate) -> CartResponse:
        """Добавление товара в корзину"""
        product = self.session.query(tables.Product).filter_by(
            id=item_data.product_id,
            is_active=True
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")

        if product.stock < item_data.quantity:
            raise HTTPException(status_code=400, detail=f"Недостаточно товара. В наличии: {product.stock}")

        cart = self._get_or_create_cart(user_id)

        cart_item = self.session.query(tables.CartItem).filter_by(
            cart_id=cart.id,
            product_id=item_data.product_id
        ).first()

        if cart_item:
            cart_item.quantity += item_data.quantity
        else:
            cart_item = tables.CartItem(
                cart_id=cart.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity
            )
            self.session.add(cart_item)

        cart.updated_at = datetime.utcnow()
        self.session.commit()

        return self._to_cart_response(cart)

    def update_cart_item(self, user_id: int, item_id: int, update_data: CartUpdate) -> CartResponse:
        """Обновление количества товара в корзине"""
        cart = self._get_or_create_cart(user_id)

        cart_item = self.session.query(tables.CartItem).filter_by(
            id=item_id,
            cart_id=cart.id
        ).first()

        if not cart_item:
            raise HTTPException(status_code=404, detail="Товар не найден в корзине")

        product = cart_item.product
        if product.stock < update_data.quantity:
            raise HTTPException(status_code=400, detail=f"Недостаточно товара. В наличии: {product.stock}")

        if update_data.quantity <= 0:
            self.session.delete(cart_item)
        else:
            cart_item.quantity = update_data.quantity

        cart.updated_at = datetime.utcnow()
        self.session.commit()

        return self._to_cart_response(cart)

    def remove_from_cart(self, user_id: int, item_id: int) -> CartResponse:
        """Удаление товара из корзины"""
        cart = self._get_or_create_cart(user_id)

        cart_item = self.session.query(tables.CartItem).filter_by(
            id=item_id,
            cart_id=cart.id
        ).first()

        if not cart_item:
            raise HTTPException(status_code=404, detail="Товар не найден в корзине")

        self.session.delete(cart_item)
        cart.updated_at = datetime.utcnow()
        self.session.commit()

        return self._to_cart_response(cart)

    def clear_cart(self, user_id: int):
        """Очистка корзины"""
        cart = self._get_or_create_cart(user_id)
        self.session.query(tables.CartItem).filter_by(cart_id=cart.id).delete()
        cart.updated_at = datetime.utcnow()
        self.session.commit()

    def checkout(self, user_id: int, checkout_data: CheckoutRequest) -> CheckoutResponse:
        """Оформление заказа из корзины"""
        cart = self._get_or_create_cart(user_id)

        if not cart.items:
            raise HTTPException(status_code=400, detail="Корзина пуста")

        # Проверяем остатки и формируем список товаров
        order_items = []
        for item in cart.items:
            product = item.product
            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Товара '{product.name}' недостаточно. В наличии: {product.stock}"
                )

            order_items.append({
                "id": product.id,
                "name": product.name,
                "quantity": item.quantity,
                "price": product.price,
                "total": product.price * item.quantity
            })

            # Уменьшаем остатки
            product.stock -= item.quantity

        total_amount = sum(item["total"] for item in order_items)

        # Создаём заказ через OrderService
        order_service = OrderService(self.session)
        order_data = {
            "customer_name": checkout_data.customer_name,
            "customer_phone": checkout_data.customer_phone,
            "customer_address": checkout_data.customer_address,
            "items": order_items,
            "total_amount": total_amount
        }

        order = order_service.create_order(user_id, order_data)

        # Очищаем корзину
        self.session.query(tables.CartItem).filter_by(cart_id=cart.id).delete()
        cart.updated_at = datetime.utcnow()
        self.session.commit()

        return CheckoutResponse(
            order={
                "order_number": order.order_number,
                "pickup_code": order.pickup_code,
                "delivery_code": order.delivery_code,
                "total_amount": order.total_amount,
                "items": order_items,
                "status": order.status,
                "store_address": order.store_address,
                "customer_address": order.customer_address,
                "customer_name": order.customer_name,
                "customer_phone": order.customer_phone
            },
            message="Заказ успешно оформлен! Сообщите код получения в магазине и код доставки клиенту."
        )