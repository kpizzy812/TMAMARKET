"""
Сервис управления остатками товаров
Резервирование, восстановление, уведомления о низком остатке
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from loguru import logger

from app.models.product import Product
from app.core.config import marketplace_settings
from app.services.telegram.message_service import MessageService


class ProductStockService:
    """Сервис для управления остатками товаров"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.message_service = MessageService()

    async def update_stock(self, product_id: int, new_quantity: int) -> bool:
        """
        Обновление остатка товара

        Args:
            product_id: ID товара
            new_quantity: Новое количество

        Returns:
            True если обновлено успешно
        """
        try:
            product = await self._get_product(product_id)
            if not product:
                return False

            old_quantity = product.stock_quantity
            product.stock_quantity = new_quantity

            await self.session.commit()

            # Проверяем уведомление о низком остатке
            await self._check_low_stock_notification(product)

            logger.info(f"📦 Остаток товара {product.name}: {old_quantity} → {new_quantity}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка обновления остатка товара {product_id}: {e}")
            await self.session.rollback()
            return False

    async def reserve_stock(self, product_id: int, quantity: int) -> bool:
        """
        Резервирование товара (уменьшение остатка)

        Args:
            product_id: ID товара
            quantity: Количество для резервирования

        Returns:
            True если зарезервировано успешно
        """
        try:
            product = await self._get_product(product_id)
            if not product:
                logger.warning(f"⚠️ Товар {product_id} не найден для резервирования")
                return False

            if not product.can_order_quantity(quantity):
                logger.warning(f"⚠️ Недостаточно товара {product.name} для резервирования {quantity}")
                return False

            success = await product.update_stock(-quantity)
            if not success:
                return False

            await self.session.commit()

            logger.info(f"📦 Зарезервировано {quantity} шт. товара {product.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка резервирования товара {product_id}: {e}")
            await self.session.rollback()
            return False

    async def restore_stock(self, product_id: int, quantity: int) -> bool:
        """
        Восстановление товара (увеличение остатка)

        Args:
            product_id: ID товара
            quantity: Количество для восстановления

        Returns:
            True если восстановлено успешно
        """
        try:
            product = await self._get_product(product_id)
            if not product:
                return False

            success = await product.update_stock(quantity)
            if not success:
                return False

            await self.session.commit()

            logger.info(f"📦 Восстановлено {quantity} шт. товара {product.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка восстановления товара {product_id}: {e}")
            await self.session.rollback()
            return False

    async def bulk_reserve_stock(self, items: List[dict]) -> bool:
        """
        Массовое резервирование товаров (для заказа)

        Args:
            items: Список словарей {"product_id": int, "quantity": int}

        Returns:
            True если все товары зарезервированы успешно
        """
        try:
            # Сначала проверяем доступность всех товаров
            for item in items:
                product_id = item["product_id"]
                quantity = item["quantity"]

                product = await self._get_product(product_id)
                if not product:
                    logger.warning(f"⚠️ Товар {product_id} не найден")
                    return False

                if not product.can_order_quantity(quantity):
                    logger.warning(f"⚠️ Недостаточно товара {product.name} для заказа {quantity}")
                    return False

            # Если все проверки прошли, резервируем
            for item in items:
                product_id = item["product_id"]
                quantity = item["quantity"]

                product = await self._get_product(product_id)
                await product.update_stock(-quantity)

            await self.session.commit()

            logger.info(f"📦 Массово зарезервировано {len(items)} позиций")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка массового резервирования: {e}")
            await self.session.rollback()
            return False

    async def bulk_restore_stock(self, items: List[dict]) -> bool:
        """
        Массовое восстановление товаров (при отмене заказа)

        Args:
            items: Список словарей {"product_id": int, "quantity": int}

        Returns:
            True если все товары восстановлены успешно
        """
        try:
            for item in items:
                product_id = item["product_id"]
                quantity = item["quantity"]

                product = await self._get_product(product_id)
                if product:
                    await product.update_stock(quantity)

            await self.session.commit()

            logger.info(f"📦 Массово восстановлено {len(items)} позиций")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка массового восстановления: {e}")
            await self.session.rollback()
            return False

    async def get_low_stock_products(self, threshold: Optional[int] = None) -> List[Product]:
        """
        Получение товаров с низким остатком

        Args:
            threshold: Порог низкого остатка (по умолчанию из настроек)

        Returns:
            Список товаров с низким остатком
        """
        try:
            if threshold is None:
                threshold = marketplace_settings.LOW_STOCK_THRESHOLD

            query = select(Product).where(
                and_(
                    Product.is_available == True,
                    Product.stock_quantity < threshold,
                    Product.stock_quantity > 0
                )
            ).order_by(Product.stock_quantity)

            result = await self.session.execute(query)
            products = result.scalars().all()

            logger.info(f"⚠️ Товаров с низким остатком: {len(products)}")
            return products

        except Exception as e:
            logger.error(f"❌ Ошибка получения товаров с низким остатком: {e}")
            return []

    async def check_product_availability(self, product_id: int, quantity: int) -> dict:
        """
        Проверка доступности товара для заказа

        Args:
            product_id: ID товара
            quantity: Желаемое количество

        Returns:
            Словарь с информацией о доступности
        """
        try:
            product = await self._get_product(product_id)
            if not product:
                return {
                    "available": False,
                    "reason": "Товар не найден",
                    "max_quantity": 0
                }

            if not product.is_purchasable:
                return {
                    "available": False,
                    "reason": "Товар недоступен для покупки",
                    "max_quantity": 0
                }

            if not product.can_order_quantity(quantity):
                return {
                    "available": False,
                    "reason": f"Недостаточное количество. Доступно: {product.get_max_available_quantity()}",
                    "max_quantity": product.get_max_available_quantity()
                }

            return {
                "available": True,
                "reason": "Товар доступен",
                "max_quantity": product.get_max_available_quantity()
            }

        except Exception as e:
            logger.error(f"❌ Ошибка проверки доступности товара {product_id}: {e}")
            return {
                "available": False,
                "reason": "Ошибка проверки",
                "max_quantity": 0
            }

    async def get_stock_movements_summary(self, product_id: int) -> dict:
        """
        Получение сводки движения остатков товара

        Args:
            product_id: ID товара

        Returns:
            Словарь со статистикой движения остатков
        """
        try:
            product = await self._get_product(product_id)
            if not product:
                return {}

            # TODO: Добавить запросы к истории заказов для получения статистики
            # reserved_quantity = await self._get_reserved_quantity(product_id)
            # total_sold = await self._get_total_sold(product_id)

            return {
                "current_stock": product.stock_quantity,
                "is_low_stock": product.is_low_stock,
                "is_in_stock": product.is_in_stock,
                "max_order_quantity": product.get_max_available_quantity(),
                "reserved_quantity": 0,  # TODO
                "total_sold": 0,  # TODO
                "stock_status": product.stock_status
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения сводки остатков товара {product_id}: {e}")
            return {}

    async def _get_product(self, product_id: int) -> Optional[Product]:
        """Получение товара по ID"""
        try:
            query = select(Product).where(Product.id == product_id)
            result = await self.session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Ошибка получения товара {product_id}: {e}")
            return None

    async def _check_low_stock_notification(self, product: Product) -> None:
        """
        Проверка и отправка уведомления о низком остатке

        Args:
            product: Товар для проверки
        """
        try:
            if product.is_low_stock and product.stock_quantity > 0:
                message = (
                    f"⚠️ *Низкий остаток товара*\n\n"
                    f"📦 *Товар:* {product.name}\n"
                    f"📊 *Остаток:* {product.stock_quantity} шт.\n"
                    f"💰 *Цена:* {product.display_price}\n\n"
                    f"Рекомендуется пополнить остаток товара."
                )

                await self.message_service.send_admin_notification(message)
                logger.warning(f"⚠️ Отправлено уведомление о низком остатке: {product.name}")

        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления о низком остатке: {e}")

    # TODO: Методы для работы с историей движения остатков
    # async def _get_reserved_quantity(self, product_id: int) -> int:
    # async def _get_total_sold(self, product_id: int) -> int:
    # async def create_stock_movement_record(self, product_id: int, movement_type: str, quantity: int, reason: str):