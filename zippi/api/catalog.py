from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from ..model.auth import User
from ..model.catalog import CategoryCreate, CategoryResponse, ProductCreate, ProductResponse
from ..service.auth import get_current_user
from ..service.catalog import CatalogService

router = APIRouter(prefix='/catalog', tags=['Каталог'])


# ========== Категории ==========
@router.get('/categories', response_model=List[CategoryResponse])
def get_categories(
    active_only: bool = True,
    service: CatalogService = Depends()
):
    """Получение списка категорий"""
    return service.get_categories(active_only)


@router.get('/categories/{category_id}', response_model=CategoryResponse)
def get_category(category_id: int, service: CatalogService = Depends()):
    """Получение категории по ID"""
    return service.get_category(category_id)


@router.post('/categories', response_model=CategoryResponse)
def create_category(
    category_data: CategoryCreate,
    user: User = Depends(get_current_user),
    service: CatalogService = Depends()
):
    """Создание категории (только для админа)"""
    # TODO: добавить проверку is_admin
    return service.create_category(category_data)


@router.put('/categories/{category_id}', response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryCreate,
    user: User = Depends(get_current_user),
    service: CatalogService = Depends()
):
    """Обновление категории (только для админа)"""
    return service.update_category(category_id, category_data)


@router.delete('/categories/{category_id}')
def delete_category(
    category_id: int,
    user: User = Depends(get_current_user),
    service: CatalogService = Depends()
):
    """Удаление категории (только для админа)"""
    return service.delete_category(category_id)


# ========== Товары ==========
@router.get('/products', response_model=List[ProductResponse])
def get_products(
    category_id: Optional[int] = Query(None, description="Фильтр по категории"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    active_only: bool = True,
    service: CatalogService = Depends()
):
    """Получение списка товаров"""
    return service.get_products(category_id, active_only, search)


@router.get('/products/{product_id}', response_model=ProductResponse)
def get_product(product_id: int, service: CatalogService = Depends()):
    """Получение товара по ID"""
    return service.get_product(product_id)


@router.post('/products', response_model=ProductResponse)
def create_product(
    product_data: ProductCreate,
    user: User = Depends(get_current_user),
    service: CatalogService = Depends()
):
    """Создание товара (только для админа)"""
    return service.create_product(product_data)


@router.put('/products/{product_id}', response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductCreate,
    user: User = Depends(get_current_user),
    service: CatalogService = Depends()
):
    """Обновление товара (только для админа)"""
    return service.update_product(product_id, product_data)


@router.patch('/products/{product_id}/stock', response_model=ProductResponse)
def update_stock(
    product_id: int,
    stock: int = Query(..., description="Новое количество"),
    user: User = Depends(get_current_user),
    service: CatalogService = Depends()
):
    """Обновление остатков товара"""
    return service.update_product_stock(product_id, stock)


@router.delete('/products/{product_id}')
def delete_product(
    product_id: int,
    user: User = Depends(get_current_user),
    service: CatalogService = Depends()
):
    """Удаление товара (только для админа)"""
    return service.delete_product(product_id)