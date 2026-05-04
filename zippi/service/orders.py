import random
import json
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from typing import List, Optional

from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from ..database import get_session
from ..model.orders import OrderCreate, OrderResponse, OrderCard, ShiftCreate, ShiftResponse, OrderItem
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

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Расчет расстояния между двумя точками (в километрах)"""
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return round(R * c, 2)

    def create_order(self, order_data: OrderCreate) -> OrderResponse:
        """Создание нового заказа"""
        order_number = self.generate_order_number()
        pickup_code = self.generate_code()
        delivery_code = self.generate_code()

        order = tables.Order(
            order_number=order_number,
            pickup_code=pickup_code,
            delivery_code=delivery_code,
            store_address=order_data.store_address,
            store_latitude=order_data.store_latitude,
            store_longitude=order_data.store_longitude,
            customer_address=order_data.customer_address,
            customer_latitude=order_data.customer_latitude,
            customer_longitude=order_data.customer_longitude,
            customer_phone=order_data.customer_phone,
            customer_name=order_data.customer_name,
            items=json.dumps([item.model_dump() for item in order_data.items]),
            total_amount=order_data.total_amount,
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
            items=[OrderItem(**item) for item in items],
            total_amount=order.total_amount or 0,
            status=order.status,
            is_active=order.is_active,
            created_at=order.created_at,
            ready_at=order.ready_at,
            picked_up_at=order.picked_up_at,
            delivered_at=order.delivered_at,
            courier_id=order.courier_id
        )

    def get_available_orders(self, courier_lat: Optional[float] = None, courier_lon: Optional[float] = None) -> List[
        OrderCard]:
        """Получение списка доступных заказов"""
        orders = self.session.query(tables.Order).filter(
            tables.Order.status.in_(['pending', 'ready']),
            tables.Order.is_active == True,
            tables.Order.courier_id.is_(None)
        ).all()

        result = []
        for order in orders:
            distance = None
            if courier_lat and courier_lon and order.store_latitude and order.store_longitude:
                distance = self.calculate_distance(
                    courier_lat, courier_lon,
                    order.store_latitude, order.store_longitude
                )

            result.append(OrderCard(
                id=order.id,
                order_number=order.order_number,
                store_address=order.store_address,
                customer_address=order.customer_address,
                status=order.status,
                distance=distance
            ))

        # Сортировка по расстоянию
        result.sort(key=lambda x: x.distance if x.distance is not None else float('inf'))
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

    def start_shift(self, courier_id: int, shift_data: ShiftCreate) -> ShiftResponse:
        """Начало смены курьера"""
        # Проверяем активную смену
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

    def get_shift_info(self, courier_id: int) -> Optional[ShiftResponse]:
        """Получение информации о текущей смене"""
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

    def get_active_order(self, courier_id: int) -> Optional[OrderResponse]:
        """Получение активного заказа курьера"""
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