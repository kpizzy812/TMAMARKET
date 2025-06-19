"""
API эндпоинты v1
"""

# Экспортируем все роутеры для удобства импорта
from . import (
    admin,
    cart,
    orders,
    products,
    promocodes,
    users,
    webhook
)

__all__ = [
    "admin",
    "cart",
    "orders",
    "products",
    "promocodes",
    "users",
    "webhook"
]