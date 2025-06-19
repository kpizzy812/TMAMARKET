"""
Главный API роутер
Объединяет все эндпоинты API v1
"""

from fastapi import APIRouter
from loguru import logger

# Импорт всех роутеров эндпоинтов
from app.api.v1.endpoints import (
    products,
    users,
    cart,
    orders,
    promocodes,
    admin,
    webhook
)

# Создание главного роутера
api_router = APIRouter()

# Подключение роутеров с префиксами и тегами
routers_config = [
    {
        "router": products.router,
        "prefix": "/products",
        "tags": ["Товары"],
        "description": "Управление каталогом товаров"
    },
    {
        "router": users.router,
        "prefix": "/users",
        "tags": ["Пользователи"],
        "description": "Управление пользователями"
    },
    {
        "router": cart.router,
        "prefix": "/cart",
        "tags": ["Корзина"],
        "description": "Управление корзиной покупок"
    },
    {
        "router": orders.router,
        "prefix": "/orders",
        "tags": ["Заказы"],
        "description": "Управление заказами"
    },
    {
        "router": promocodes.router,
        "prefix": "/promocodes",
        "tags": ["Промокоды"],
        "description": "Система промокодов и скидок"
    },
    {
        "router": admin.router,
        "prefix": "/admin",
        "tags": ["Администрирование"],
        "description": "Административные функции"
    },
    {
        "router": webhook.router,
        "prefix": "/webhook",
        "tags": ["Webhook"],
        "description": "Webhook эндпоинты"
    }
]

# Подключение всех роутеров
for config in routers_config:
    api_router.include_router(
        config["router"],
        prefix=config["prefix"],
        tags=config["tags"]
    )

    logger.info(f"📍 Подключен роутер: {config['prefix']} - {config['description']}")

logger.success("🔗 Все API роутеры подключены")