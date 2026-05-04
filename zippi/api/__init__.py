from fastapi import APIRouter
from .auth import router as auth_router
from .orders import router as orders_router
from .catalog import router as catalog_router
from .cart import router as cart_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(orders_router)
router.include_router(catalog_router)
router.include_router(cart_router)