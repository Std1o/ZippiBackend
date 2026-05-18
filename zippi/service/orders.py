import random
import json
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..model.orders import OrderResponse, OrderCard, ShiftCreate, ShiftResponse, OrderStatus
from ..service.websocket_manager import manager
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

    async def _notify_order_update(self, order: tables.Order):
        """Отправка уведомления об обновлении заказа через WebSocket"""
        order_response = self._to_response(order)
        await manager.send_order_update(
            order.order_number,
            order_response.model_dump(mode='json')
        )

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
            status=OrderStatus.PENDING.value
        )

        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)

        return self._to_response(order)

    def _to_response(self, order: tables.Order) -> OrderResponse:
        """Преобразование модели БД в ответ API"""
        items = json.loads(order.items) if order.items else []

        # Получаем данные курьера, если он назначен
        courier_name = None
        courier_phone = None
        if order.courier_id:
            courier = self.session.query(tables.User).filter_by(id=order.courier_id).first()
            if courier:
                courier_name = courier.username
                courier_phone = courier.phone

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
            status=OrderStatus(order.status),  # Конвертируем строку в Enum
            is_active=order.is_active,
            created_at=order.created_at,
            picked_up_at=order.picked_up_at,
            delivered_at=order.delivered_at,
            courier_id=order.courier_id,
            courier_name=courier_name,
            courier_phone=courier_phone
        )

    # ========== Смены ==========
    def start_shift(self, courier_id: int, shift_data: ShiftCreate) -> ShiftResponse:
        """Начало смены курьера"""
        active_shift = self.session.query(tables.Shift).filter_by(
            courier_id=courier_id,
            is_active=True
        ).first()

        if active_shift:
            raise HTTPException(status_code=400, detail="У вас уже есть активная смена")

        shift = tables.Shift(
            courier_id=courier_id,
            start_time=datetime.utcnow(),
            duration_hours=shift_data.duration_hours,
            is_active=True
        )

        self.session.add(shift)
        self.session.commit()
        self.session.refresh(shift)

        return ShiftResponse(
            id=shift.id,
            start_time=shift.start_time,
            end_time=shift.end_time,
            duration_hours=shift.duration_hours,
            is_active=shift.is_active
        )

    def end_shift(self, courier_id: int) -> ShiftResponse:
        """Завершение смены курьера"""
        shift = self.session.query(tables.Shift).filter_by(
            courier_id=courier_id,
            is_active=True
        ).first()

        if not shift:
            raise HTTPException(status_code=404, detail="Нет активной смены")

        shift.end_time = datetime.utcnow()
        shift.is_active = False
        self.session.commit()
        self.session.refresh(shift)

        return ShiftResponse(
            id=shift.id,
            start_time=shift.start_time,
            end_time=shift.end_time,
            duration_hours=shift.duration_hours,
            is_active=shift.is_active
        )

    def get_current_shift(self, courier_id: int) -> Optional[ShiftResponse]:
        """Получение текущей смены курьера"""
        shift = self.session.query(tables.Shift).filter_by(
            courier_id=courier_id,
            is_active=True
        ).first()

        if shift:
            return ShiftResponse(
                id=shift.id,
                start_time=shift.start_time,
                end_time=shift.end_time,
                duration_hours=shift.duration_hours,
                is_active=shift.is_active
            )
        return None

    def is_shift_active(self, courier_id: int) -> bool:
        """Проверка, активна ли смена у курьера"""
        shift = self.session.query(tables.Shift).filter_by(
            courier_id=courier_id,
            is_active=True
        ).first()
        return shift is not None

    # ========== Заказы ==========
    def get_available_orders(self, courier_id: Optional[int] = None) -> List[OrderCard]:
        """Получение списка доступных заказов для курьеров"""
        if courier_id and not self.is_shift_active(courier_id):
            raise HTTPException(status_code=403, detail="У вас нет активной смены. Начните смену чтобы видеть заказы")

        orders = self.session.query(tables.Order).filter(
            tables.Order.status == OrderStatus.PENDING.value,
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
                status=OrderStatus(order.status)
            ))

        return result

    async def take_order(self, order_id: int, courier_id: int) -> OrderResponse:
        """Взять заказ в работу"""
        if not self.is_shift_active(courier_id):
            raise HTTPException(status_code=403, detail="У вас нет активной смены. Начните смену чтобы взять заказ")

        order = self.session.query(tables.Order).filter_by(id=order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.courier_id is not None:
            raise HTTPException(status_code=400, detail="Заказ уже взят другим курьером")

        if order.status != OrderStatus.PENDING.value:
            raise HTTPException(status_code=400, detail=f"Заказ нельзя взять (статус: {order.status})")

        # Назначаем курьера И меняем статус
        order.courier_id = courier_id
        order.status = OrderStatus.PICKED_UP.value  # Меняем статус сразу
        order.picked_up_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(order)

        # Отправляем обновление через WebSocket
        await self._notify_order_update(order)

        return self._to_response(order)

    async def confirm_pickup(self, order_number: str, pickup_code: str, courier_id: int) -> OrderResponse:
        """Подтверждение получения заказа в магазине по коду"""
        if not self.is_shift_active(courier_id):
            raise HTTPException(status_code=403, detail="У вас нет активной смены")

        order = self.session.query(tables.Order).filter_by(order_number=order_number).first()
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.courier_id != courier_id:
            raise HTTPException(status_code=403, detail="Это не ваш заказ")

        if order.pickup_code != pickup_code:
            raise HTTPException(status_code=400, detail="Неверный код получения")

        if order.status != OrderStatus.PENDING.value:
            raise HTTPException(status_code=400, detail=f"Заказ нельзя получить (статус: {order.status})")

        order.status = OrderStatus.PICKED_UP.value
        order.picked_up_at = datetime.utcnow()
        self.session.commit()
        self.session.refresh(order)

        # Отправляем обновление через WebSocket
        await self._notify_order_update(order)

        return self._to_response(order)

    async def confirm_delivery(self, order_number: str, delivery_code: str, courier_id: int) -> OrderResponse:
        """Подтверждение доставки заказа по коду клиента"""
        if not self.is_shift_active(courier_id):
            raise HTTPException(status_code=403, detail="У вас нет активной смены")

        order = self.session.query(tables.Order).filter_by(order_number=order_number).first()
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.courier_id != courier_id:
            raise HTTPException(status_code=403, detail="Это не ваш заказ")

        if order.delivery_code != delivery_code:
            raise HTTPException(status_code=400, detail="Неверный код доставки")

        if order.status != OrderStatus.PICKED_UP.value:
            raise HTTPException(status_code=400, detail=f"Заказ нельзя доставить (статус: {order.status})")

        order.status = OrderStatus.DELIVERED.value
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

        # Отправляем обновление через WebSocket
        await self._notify_order_update(order)

        return self._to_response(order)

    def get_active_order(self, courier_id: int) -> Optional[OrderResponse]:
        """Получение активного заказа курьера (который он везёт)"""
        order = self.session.query(tables.Order).filter(
            tables.Order.courier_id == courier_id,
            tables.Order.status == OrderStatus.PICKED_UP.value
        ).first()

        if order:
            return self._to_response(order)
        return None

    def get_active_order_for_customer(self, user_id: int) -> Optional[OrderResponse]:
        """Получение активного заказа клиента (который он ожидает)"""
        order = self.session.query(tables.Order).filter(
            tables.Order.user_id == user_id,
            tables.Order.status.in_([
                OrderStatus.PENDING.value,
                OrderStatus.PICKED_UP.value
            ]),
            tables.Order.is_active == True
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

    def get_orders(self) -> List[OrderResponse]:
        """Получение всех заказов курьера"""
        orders = self.session.query(tables.Order).all()
        return [self._to_response(order) for order in orders]

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

    async def remove_courier_from_order(self, order_number: str) -> OrderResponse:
        """
        Снять заказ с курьера (для администратора)
        """

        order = self.session.query(tables.Order).filter_by(order_number=order_number).first()
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        # Заказ можно снять только если он не доставлен и не отменен
        if order.status == OrderStatus.DELIVERED.value:
            raise HTTPException(status_code=400, detail="Нельзя снять доставленный заказ")

        if order.status == OrderStatus.CANCELLED.value:
            raise HTTPException(status_code=400, detail="Заказ уже отменен")

        old_courier_id = order.courier_id

        # Снимаем курьера и возвращаем статус в ожидание
        order.courier_id = None
        order.status = OrderStatus.PENDING.value
        order.picked_up_at = None
        self.session.commit()
        self.session.refresh(order)

        # Отправляем обновление через WebSocket
        await self._notify_order_update(order)

        return self._to_response(order)

    async def cancel_order(self, order_number: str) -> OrderResponse:
        """
        Отменить заказ (для администратора)
        """

        order = self.session.query(tables.Order).filter_by(order_number=order_number).first()
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.status == OrderStatus.DELIVERED.value:
            raise HTTPException(status_code=400, detail="Нельзя отменить доставленный заказ")

        # Отменяем заказ
        order.status = OrderStatus.CANCELLED.value
        order.is_active = False
        order.courier_id = None
        self.session.commit()
        self.session.refresh(order)

        # Отправляем обновление через WebSocket
        await self._notify_order_update(order)

        return self._to_response(order)

    async def remove_item_from_order(self, order_number: str, product_id: int) -> OrderResponse:
        """
        Удалить товар из заказа (для администратора)
        """
        # Проверка прав администратора (опционально)

        order = self.session.query(tables.Order).filter_by(order_number=order_number).first()
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")

        if order.status != OrderStatus.PENDING.value:
            raise HTTPException(status_code=400, detail=f"Нельзя изменять заказ в статусе {order.status}")

        # Загружаем текущие товары
        items = json.loads(order.items)

        # Ищем товар для удаления
        item_to_remove = None
        for item in items:
            if item.get('id') == product_id:
                item_to_remove = item
                break

        if not item_to_remove:
            raise HTTPException(status_code=404, detail="Товар не найден в заказе")

        # Удаляем товар
        new_items = [item for item in items if item.get('product_id') != product_id]

        # Пересчитываем общую сумму
        total_amount = sum(item.get('price', 0) * item.get('quantity', 1) for item in new_items)

        # Обновляем заказ
        order.items = json.dumps(new_items)
        order.total_amount = total_amount

        # Если товаров не осталось - отменяем заказ
        if not new_items:
            order.is_active = False
            order.status = OrderStatus.CANCELLED.value

        self.session.commit()
        self.session.refresh(order)

        # Отправляем обновление через WebSocket
        await self._notify_order_update(order)

        return self._to_response(order)