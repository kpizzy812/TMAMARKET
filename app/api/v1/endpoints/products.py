"""
API эндпоинты для работы с товарами
"""

from fastapi import APIRouter
from loguru import logger

router = APIRouter()

@router.get("/")
async def get_products():
    """Получение списка товаров"""
    logger.info("📦 Запрос списка товаров")
    return {"message": "Products endpoint - TODO"}

@router.get("/{product_id}")
async def get_product(product_id: int):
    """Получение товара по ID"""
    logger.info(f"📦 Запрос товара ID: {product_id}")
    return {"message": f"Product {product_id} - TODO"}