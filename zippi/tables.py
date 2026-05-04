from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True)
    phone = sa.Column(sa.Text, unique=True, nullable=False)
    username = sa.Column(sa.Text)
    password_hash = sa.Column(sa.Text)
    is_courier = sa.Column(sa.Boolean, default=True)


class Order(Base):
    __tablename__ = 'orders'
    id = sa.Column(sa.Integer, primary_key=True)
    order_number = sa.Column(sa.String(6), unique=True, nullable=False)  # 6 цифр
    pickup_code = sa.Column(sa.String(4), nullable=False)  # 4 цифры для получения в магазине
    delivery_code = sa.Column(sa.String(4), nullable=False)  # 4 цифры для подтверждения доставки

    # Адрес магазина
    store_address = sa.Column(sa.String(500), nullable=False)
    store_latitude = sa.Column(sa.Float)
    store_longitude = sa.Column(sa.Float)

    # Адрес клиента
    customer_address = sa.Column(sa.String(500), nullable=False)
    customer_latitude = sa.Column(sa.Float)
    customer_longitude = sa.Column(sa.Float)
    customer_phone = sa.Column(sa.String(20), nullable=False)
    customer_name = sa.Column(sa.String(200))

    # Информация о заказе
    items = sa.Column(sa.Text, nullable=False)  # JSON строка со списком товаров
    total_amount = sa.Column(sa.Float)

    # Статусы заказа
    status = sa.Column(sa.String(50), default='pending')  # pending, ready, picked_up, delivered, cancelled
    is_active = sa.Column(sa.Boolean, default=True)

    # Временные метки
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    ready_at = sa.Column(sa.DateTime)
    picked_up_at = sa.Column(sa.DateTime)
    delivered_at = sa.Column(sa.DateTime)

    # Связи
    courier_id = sa.Column(sa.Integer, ForeignKey('users.id'), nullable=True)
    courier = relationship("User", backref="orders", foreign_keys=[courier_id])


class Shift(Base):
    __tablename__ = 'shifts'
    id = sa.Column(sa.Integer, primary_key=True)
    courier_id = sa.Column(sa.Integer, ForeignKey('users.id'), nullable=False)
    start_time = sa.Column(sa.DateTime, nullable=False)
    end_time = sa.Column(sa.DateTime)
    duration_hours = sa.Column(sa.Integer)
    is_active = sa.Column(sa.Boolean, default=True)

    courier = relationship("User", backref="shifts")


class DeliveryHistory(Base):
    __tablename__ = 'delivery_history'
    id = sa.Column(sa.Integer, primary_key=True)
    order_id = sa.Column(sa.Integer, ForeignKey('orders.id'), nullable=False)
    courier_id = sa.Column(sa.Integer, ForeignKey('users.id'), nullable=False)
    delivery_address = sa.Column(sa.String(500))
    delivery_time = sa.Column(sa.DateTime, default=datetime.utcnow)

    order = relationship("Order")
    courier = relationship("User")