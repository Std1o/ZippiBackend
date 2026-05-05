from datetime import datetime
import json

import sqlalchemy as sa
from sqlalchemy import Float, ForeignKey, Text, Boolean, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True)
    phone = sa.Column(sa.Text, unique=True, nullable=False)
    username = sa.Column(sa.Text)
    password_hash = sa.Column(sa.Text)
    is_courier = sa.Column(sa.Boolean, default=False)
    is_admin = sa.Column(sa.Boolean, default=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)


class Category(Base):
    __tablename__ = 'categories'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(100), nullable=False)
    description = sa.Column(sa.Text)
    image_url = sa.Column(sa.String(500))
    sort_order = sa.Column(sa.Integer, default=0)
    is_active = sa.Column(sa.Boolean, default=True)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = 'products'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(200), nullable=False)
    description = sa.Column(sa.Text)
    price = sa.Column(sa.Float, nullable=False)
    old_price = sa.Column(sa.Float)
    image_url = sa.Column(sa.String(500))
    category_id = sa.Column(sa.Integer, ForeignKey('categories.id'))
    stock = sa.Column(sa.Integer, default=0)
    is_active = sa.Column(sa.Boolean, default=True)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="products")


class Cart(Base):
    __tablename__ = 'carts'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, ForeignKey('users.id'), nullable=False)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = 'cart_items'
    id = sa.Column(sa.Integer, primary_key=True)
    cart_id = sa.Column(sa.Integer, ForeignKey('carts.id'), nullable=False)
    product_id = sa.Column(sa.Integer, ForeignKey('products.id'), nullable=False)
    quantity = sa.Column(sa.Integer, default=1)
    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


class Order(Base):
    __tablename__ = 'orders'
    id = sa.Column(sa.Integer, primary_key=True)
    order_number = sa.Column(sa.String(6), unique=True, nullable=False)
    pickup_code = sa.Column(sa.String(4), nullable=False)
    delivery_code = sa.Column(sa.String(4), nullable=False)

    user_id = sa.Column(sa.Integer, ForeignKey('users.id'), nullable=False)
    courier_id = sa.Column(sa.Integer, ForeignKey('users.id'), nullable=True)

    store_address = sa.Column(sa.String(500), nullable=False)
    customer_address = sa.Column(sa.String(500), nullable=False)
    customer_phone = sa.Column(sa.String(20), nullable=False)
    customer_name = sa.Column(sa.String(200))

    items = sa.Column(sa.Text, nullable=False)
    total_amount = sa.Column(sa.Float)

    status = sa.Column(sa.String(50), default='pending')
    is_active = sa.Column(sa.Boolean, default=True)

    created_at = sa.Column(sa.DateTime, default=datetime.utcnow)
    ready_at = sa.Column(sa.DateTime)
    picked_up_at = sa.Column(sa.DateTime)
    delivered_at = sa.Column(sa.DateTime)

    user = relationship("User", foreign_keys=[user_id], backref="orders_as_customer")
    courier = relationship("User", foreign_keys=[courier_id], backref="orders_as_courier")


class Shift(Base):
    __tablename__ = 'shifts'
    id = sa.Column(sa.Integer, primary_key=True)
    courier_id = sa.Column(sa.Integer, ForeignKey('users.id'), nullable=False)
    start_time = sa.Column(sa.DateTime, nullable=False)
    end_time = sa.Column(sa.DateTime)
    duration_hours = sa.Column(sa.Integer)
    is_active = sa.Column(sa.Boolean, default=True)

    courier = relationship("User", foreign_keys=[courier_id], backref="shifts")


class DeliveryHistory(Base):
    __tablename__ = 'delivery_history'
    id = sa.Column(sa.Integer, primary_key=True)
    order_id = sa.Column(sa.Integer, ForeignKey('orders.id'), nullable=False)
    courier_id = sa.Column(sa.Integer, ForeignKey('users.id'), nullable=False)
    delivery_address = sa.Column(sa.String(500))
    delivery_time = sa.Column(sa.DateTime, default=datetime.utcnow)

    order = relationship("Order")
    courier = relationship("User", foreign_keys=[courier_id])