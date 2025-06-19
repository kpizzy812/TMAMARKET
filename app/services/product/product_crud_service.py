"""
CRUD сервис для товаров
Базовые операции создания, чтения, обновления и удаления
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger

from app.models.product import Product
from app.schemas.product import ProductCreateSchema, ProductUpdateSchema


class ProductCRUDService:
    """Сервис для базовых CRUD операций с товарами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, product_id: int, increment_views: bool = True) -> Optional[Product]:
        """
        Получение товара по ID

        Args:
            product_id: ID товара
            increment_views: Увеличивать ли счетчик просмотров

        Returns:
            Product или None
        """
        try:
            query = select(Product).where(Product.id == product_id)
            result = await self.session.execute(query)
            product = result.scalar_one_or_none()

            if product and increment_views:
                product.increment_views()
                await self.session.commit()

            return product

        except Exception as e:
            logger.error(f"❌ Ошибка получения товара {product_id}: {e}")
            return None

    async def create(self, product_data: ProductCreateSchema) -> Optional[Product]:
        """
        Создание нового товара

        Args:
            product_data: Данные для создания товара

        Returns:
            Созданный товар или None
        """
        try:
            product = Product(**product_data.model_dump())

            self.session.add(product)
            await self.session.commit()
            await self.session.refresh(product)

            logger.success(f"✅ Создан товар: {product.name} (ID: {product.id})")
            return product

        except Exception as e:
            logger.error(f"❌ Ошибка создания товара: {e}")
            await self.session.rollback()
            return None

    async def update(self, product_id: int, product_data: ProductUpdateSchema) -> Optional[Product]:
        """
        Обновление товара

        Args:
            product_id: ID товара
            product_data: Данные для обновления

        Returns:
            Обновленный товар или None
        """
        try:
            product = await self.get_by_id(product_id, increment_views=False)
            if not product:
                logger.warning(f"⚠️ Товар {product_id} не найден")
                return None

            # Обновляем поля
            update_data = product_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(product, field, value)

            await self.session.commit()
            await self.session.refresh(product)

            logger.success(f"✅ Обновлен товар: {product.name} (ID: {product.id})")
            return product

        except Exception as e:
            logger.error(f"❌ Ошибка обновления товара {product_id}: {e}")
            await self.session.rollback()
            return None

    async def delete(self, product_id: int) -> bool:
        """
        Удаление товара

        Args:
            product_id: ID товара

        Returns:
            True если удален успешно
        """
        try:
            # TODO: Добавить проверку связанных заказов

            query = delete(Product).where(Product.id == product_id)
            result = await self.session.execute(query)
            await self.session.commit()

            if result.rowcount > 0:
                logger.success(f"✅ Удален товар ID: {product_id}")
                return True
            else:
                logger.warning(f"⚠️ Товар {product_id} не найден для удаления")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка удаления товара {product_id}: {e}")
            await self.session.rollback()
            return False

    async def exists(self, product_id: int) -> bool:
        """
        Проверка существования товара

        Args:
            product_id: ID товара

        Returns:
            True если товар существует
        """
        try:
            query = select(Product.id).where(Product.id == product_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.error(f"❌ Ошибка проверки существования товара {product_id}: {e}")
            return False

    async def get_stats(self, product_id: int) -> Dict[str, Any]:
        """
        Получение базовой статистики товара

        Args:
            product_id: ID товара

        Returns:
            Словарь со статистикой
        """
        try:
            product = await self.get_by_id(product_id, increment_views=False)
            if not product:
                return {}

            # TODO: Добавить запросы для получения статистики заказов
            # total_ordered_quantity = await self._get_total_ordered_quantity(product_id)
            # revenue = await self._get_product_revenue(product_id)
            # last_ordered = await self._get_last_order_date(product_id)

            return {
                "views_count": product.views_count,
                "orders_count": product.orders_count,
                "total_ordered_quantity": 0,  # TODO
                "revenue": 0.0,  # TODO
                "last_ordered": None,  # TODO
                "current_stock": product.stock_quantity,
                "is_low_stock": product.is_low_stock
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики товара {product_id}: {e}")
            return {}

    # TODO: Методы для получения статистики заказов
    # async def _get_total_ordered_quantity(self, product_id: int) -> int:
    # async def _get_product_revenue(self, product_id: int) -> float:
    # async def _get_last_order_date(self, product_id: int) -> Optional[datetime]: