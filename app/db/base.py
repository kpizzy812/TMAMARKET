"""
Импорт всех моделей для Alembic
Этот файл нужен для корректной работы миграций
"""

from app.core.database import Base

# Импортируем все модели
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.cart import Cart, CartItem
from app.models.promocode import Promocode, PromocodeUsage
from app.models.payment import Payment
from app.models.delivery import Delivery

# Все модели будут автоматически зарегистрированы в Base.metadata