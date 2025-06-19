"""
API эндпоинты для работы с промокодами
"""

from fastapi import APIRouter
from loguru import logger

router = APIRouter()

@router.post("/validate")
async def validate_promocode():
    """Проверка действительности промокода"""
    logger.info("🎫 Проверка промокода")
    return {"message": "Validate promocode - TODO"}

@router.post("/apply")
async def apply_promocode():
    """Применение промокода к корзине"""
    logger.info("🎫 Применение промокода")
    return {"message": "Apply promocode - TODO"}

@router.get("/{code}")
async def get_promocode_info(code: str):
    """Получение информации о промокоде"""
    logger.info(f"🎫 Информация о промокоде: {code}")
    return {"message": f"Promocode {code} info - TODO"}