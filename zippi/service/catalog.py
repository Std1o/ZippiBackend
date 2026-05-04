from typing import List, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database import get_session
from ..model.catalog import CategoryCreate, CategoryResponse, ProductCreate, ProductResponse
from .. import tables


class CatalogService:
    def __init__(self, session: Session = Depends(get_session)):
        self.session = session

    # ========== Категории ==========
    def create_category(self, category_data: CategoryCreate) -> CategoryResponse:
        """Создание категории"""
        category = tables.Category(
            name=category_data.name,
            description=category_data.description,
            image_url=category_data.image_url,
            sort_order=category_data.sort_order
        )
        self.session.add(category)
        self.session.commit()
        self.session.refresh(category)
        return CategoryResponse.model_validate(category)

    def get_categories(self, active_only: bool = True) -> List[CategoryResponse]:
        """Получение списка категорий"""
        query = self.session.query(tables.Category)
        if active_only:
            query = query.filter(tables.Category.is_active == True)
        categories = query.order_by(tables.Category.sort_order).all()
        return [CategoryResponse.model_validate(c) for c in categories]

    def get_category(self, category_id: int) -> CategoryResponse:
        """Получение категории по ID"""
        category = self.session.query(tables.Category).filter_by(id=category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        return CategoryResponse.model_validate(category)

    def update_category(self, category_id: int, category_data: CategoryCreate) -> CategoryResponse:
        """Обновление категории"""
        category = self.session.query(tables.Category).filter_by(id=category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")

        for key, value in category_data.model_dump().items():
            setattr(category, key, value)

        self.session.commit()
        self.session.refresh(category)
        return CategoryResponse.model_validate(category)

    def delete_category(self, category_id: int):
        """Удаление категории (soft delete)"""
        category = self.session.query(tables.Category).filter_by(id=category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")
        category.is_active = False
        self.session.commit()

    # ========== Товары ==========
    def create_product(self, product_data: ProductCreate) -> ProductResponse:
        """Создание товара"""
        # Проверяем существование категории
        category = self.session.query(tables.Category).filter_by(id=product_data.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Категория не найдена")

        product = tables.Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            old_price=product_data.old_price,
            image_url=product_data.image_url,
            category_id=product_data.category_id,
            stock=product_data.stock
        )
        self.session.add(product)
        self.session.commit()
        self.session.refresh(product)
        return ProductResponse.model_validate(product)

    def get_products(
            self,
            category_id: Optional[int] = None,
            active_only: bool = True,
            search: Optional[str] = None
    ) -> List[ProductResponse]:
        """Получение списка товаров с фильтрацией"""
        query = self.session.query(tables.Product)

        if active_only:
            query = query.filter(tables.Product.is_active == True)

        if category_id:
            query = query.filter(tables.Product.category_id == category_id)

        if search:
            query = query.filter(tables.Product.name.contains(search))

        products = query.order_by(tables.Product.created_at.desc()).all()
        return [ProductResponse.model_validate(p) for p in products]

    def get_product(self, product_id: int) -> ProductResponse:
        """Получение товара по ID"""
        product = self.session.query(tables.Product).filter_by(id=product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        return ProductResponse.model_validate(product)

    def update_product(self, product_id: int, product_data: ProductCreate) -> ProductResponse:
        """Обновление товара"""
        product = self.session.query(tables.Product).filter_by(id=product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")

        for key, value in product_data.model_dump().items():
            setattr(product, key, value)

        self.session.commit()
        self.session.refresh(product)
        return ProductResponse.model_validate(product)

    def update_product_stock(self, product_id: int, stock: int) -> ProductResponse:
        """Обновление количества товара"""
        product = self.session.query(tables.Product).filter_by(id=product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")

        product.stock = stock
        self.session.commit()
        self.session.refresh(product)
        return ProductResponse.model_validate(product)

    def delete_product(self, product_id: int):
        """Удаление товара (soft delete)"""
        product = self.session.query(tables.Product).filter_by(id=product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Товар не найден")
        product.is_active = False
        self.session.commit()