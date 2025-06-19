"""
Импорт всех моделей для Alembic
Этот файл нужен для корректной работы миграций
"""

from app.core.database import Base

# Импортируем все модели в правильном порядке (учитывая зависимости)

# Базовые модели
from app.models.user import User
from app.models.product import Product

# Промокоды
from app.models.promocode import Promocode, PromocodeUsage

# Корзина
from app.models.cart import Cart, CartItem

# Заказы (зависят от пользователей, товаров и промокодов)
from app.models.order import Order, OrderItem

# Платежи и доставка (зависят от заказов)
from app.models.payment import Payment
from app.models.delivery import Delivery

# Все модели будут автоматически зарегистрированы в Base.metadata
# Порядок импорта важен для корректного создания foreign key constraints

__all__ = [
    "Base",
    "User",
    "Product",
    "Promocode", "PromocodeUsage",
    "Cart", "CartItem",
    "Order", "OrderItem",
    "Payment",
    "Delivery"
]