import random
import json
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..model.orders import OrderResponse, OrderCard
from .. import tables


class OrderService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    def generate_order_number(self) -> str:
        """Генерация 6-значного номера заказа"""
        while True:
            number = str(random.randint(100000, 999999))
            if not self.session.query(tables.Order).filter_by(order_number=number).first():
                return number

    def generate_code(self) -> str:
        """Генерация 4-значного кода"""
        return f"{random.randint(1000, 9999)}"

    def create_order(self, user_id: int, order_data: dict) -> OrderResponse:
        """Создание нового заказа из корзины"""
        order_number = self.generate_order_number()
        pickup_code = self.generate_code()
        delivery_code = self.generate_code()

        order = tables.Order(
            order_number=order_number,
            pickup_code=pickup_code,
            delivery_code=delivery_code,
            user_id=user_id,
            store_address=order_data.get('store_address', 'Магазин одежды, ул. Центральная, 1'),
            customer_address=order_data['customer_address'],
            customer_phone=order_data['customer_phone'],
            customer_name=order_data['customer_name'],
            items=json.dumps(order_data['items']),
            total_amount=order_data['total_amount'],
            status='pending'
        )

        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)

        return self._to_response(order)

    def _to_response(self, order: tables.Order) -> OrderResponse:
        """Преобразование модели БД в ответ API"""
        items = json.loads(order.items) if order.items else []

        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            pickup_code=order.pickup_code,
            delivery_code=order.delivery_code,
            store_address=order.store_address,
            customer_address=order.customer_address,
            customer_phone=order.customer_phone,
            customer_name=order.customer_name,
            items=items,
            total_amount=order.total_amount or 0,
            status=order.status,
            is_active=order.is_active,
            created_at=order.created_at,
            ready_at=order.ready_at,
            picked_up_at=order.picked_up_at,
            delivered_at=order.delivered_at,
            courier_id=order.courier_id
        )

    def get_available_orders(self) -> List[OrderCard]:
        """Получение списка доступных заказов для курьеров (без сортировки по расстоянию)"""
        orders = self.session.query(tables.Order).filter(
            tables.Order.status.in_(['pending', 'ready']),
            tables.Order.is_active == True,
            tables.Order.courier_id.is_(None)
        ).order_by(tables.Order.created_at.asc()).all()

        result = []
        for order in orders:
            result.append(OrderCard(
                id=order.id,
                order_number=order.order_number,
                store_address=order.store_address,
                customer_address=order.customer_address,
                status=order.status
            ))

        return result

    def take_order(self, order_id: int, courier_id: int) -> OrderResponse:
        """Взять заказ в работу"""
        order = self.session.query(tables.Order).filter_by(id=order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.courier_id is not None:
            raise HTTPException(status_code=400, detail="Заказ уже взят другим курьером")

        if order.status not in ['pending', 'ready']:
            raise HTTPException(status_code=400, detail=f"Заказ нельзя взять (статус: {order.status})")

        order.courier_id = courier_id
        self.session.commit()
        self.session.refresh(order)

        return self._to_response(order)

    def confirm_pickup(self, order_number: str, pickup_code: str, courier_id: int) -> OrderResponse:
        """Подтверждение получения заказа в магазине по коду"""
        order = self.session.query(tables.Order).filter_by(order_number=order_number).first()
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.courier_id != courier_id:
            raise HTTPException(status_code=403, detail="Это не ваш заказ")

        if order.pickup_code != pickup_code:
            raise HTTPException(status_code=400, detail="Неверный код получения")

        if order.status != 'ready':
            raise HTTPException(status_code=400, detail=f"Заказ не готов к выдаче (статус: {order.status})")

        order.status = 'picked_up'
        order.picked_up_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(order)

        return self._to_response(order)

    def confirm_delivery(self, order_number: str, delivery_code: str, courier_id: int) -> OrderResponse:
        """Подтверждение доставки заказа по коду клиента"""
        order = self.session.query(tables.Order).filter_by(order_number=order_number).first()
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.courier_id != courier_id:
            raise HTTPException(status_code=403, detail="Это не ваш заказ")

        if order.delivery_code != delivery_code:
            raise HTTPException(status_code=400, detail="Неверный код доставки")

        if order.status != 'picked_up':
            raise HTTPException(status_code=400, detail=f"Заказ нельзя доставить (статус: {order.status})")

        order.status = 'delivered'
        order.delivered_at = datetime.utcnow()
        order.is_active = False
        self.session.commit()
        self.session.refresh(order)

        # Добавляем в историю
        history = tables.DeliveryHistory(
            order_id=order.id,
            courier_id=courier_id,
            delivery_address=order.customer_address,
            delivery_time=datetime.utcnow()
        )
        self.session.add(history)
        self.session.commit()

        return self._to_response(order)

    def update_order_status(self, order_number: str, status: str) -> OrderResponse:
        """Обновление статуса заказа (для магазина)"""
        order = self.session.query(tables.Order).filter_by(order_number=order_number).first()
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if status == 'ready' and order.status == 'pending':
            order.status = 'ready'
            order.ready_at = datetime.utcnow()
        elif status == 'cancelled':
            order.status = 'cancelled'
            order.is_active = False
        else:
            raise HTTPException(status_code=400, detail=f"Нельзя изменить статус с {order.status} на {status}")

        self.session.commit()
        self.session.refresh(order)

        return self._to_response(order)

    def get_active_order(self, courier_id: int) -> Optional[OrderResponse]:
        """Получение активного заказа курьера (который он везёт)"""
        order = self.session.query(tables.Order).filter(
            tables.Order.courier_id == courier_id,
            tables.Order.status == 'picked_up'
        ).first()

        if order:
            return self._to_response(order)
        return None

    def get_order_history(self, courier_id: int) -> List[dict]:
        """Получение истории доставок курьера"""
        history = self.session.query(tables.DeliveryHistory).filter_by(
            courier_id=courier_id
        ).order_by(tables.DeliveryHistory.delivery_time.desc()).all()

        result = []
        for record in history:
            order = self.session.query(tables.Order).filter_by(id=record.order_id).first()
            result.append({
                'address': record.delivery_address,
                'delivery_time': record.delivery_time,
                'order_number': order.order_number if order else None
            })

        return result

    def get_my_orders(self, courier_id: int) -> List[OrderResponse]:
        """Получение всех заказов курьера"""
        orders = self.session.query(tables.Order).filter_by(courier_id=courier_id).all()
        return [self._to_response(order) for order in orders]

    def get_order_by_number(self, order_number: str) -> Optional[OrderResponse]:
        """Получение заказа по номеру"""
        order = self.session.query(tables.Order).filter_by(order_number=order_number).first()
        if order:
            return self._to_response(order)
        return None

    def get_my_orders_as_customer(self, user_id: int) -> List[OrderResponse]:
        """Получение заказов пользователя (как клиента)"""
        orders = self.session.query(tables.Order).filter_by(user_id=user_id).all()
        return [self._to_response(order) for order in orders]