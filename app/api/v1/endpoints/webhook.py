"""
API эндпоинты для webhook'ов
"""

from fastapi import APIRouter, Request
from loguru import logger

router = APIRouter()

@router.post("/payment")
async def payment_webhook(request: Request):
    """Webhook для уведомлений о платежах"""
    logger.info("💳 Payment webhook")
    return {"message": "Payment webhook - TODO"}

@router.post("/delivery")
async def delivery_webhook(request: Request):
    """Webhook для уведомлений о доставке"""
    logger.info("📦 Delivery webhook")
    return {"message": "Delivery webhook - TODO"}