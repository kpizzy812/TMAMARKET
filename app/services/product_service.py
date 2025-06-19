"""
Сервис для работы с товарами
Управление каталогом, остатками, изображениями
"""

import os
import aiofiles
from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload
from loguru import logger

from app.models.product import Product
from app.schemas.product import (
    ProductCreateSchema,
    ProductUpdateSchema,
    ProductFilterSchema
)
from app.core.config import marketplace_settings
from app.services.telegram.message_service import MessageService


class ProductService:
    """Сервис для работы с товарами"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.message_service = MessageService()

    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Получение товара по ID

        Args:
            product_id: ID товара

        Returns:
            Product или None
        """
        try:
            query = select(Product).where(Product.id == product_id)
            result = await self.session.execute(query)
            product = result.scalar_one_or_none()

            if product:
                # Увеличиваем счетчик просмотров
                product.increment_views()
                await self.session.commit()

            return product

        except Exception as e:
            logger.error(f"❌ Ошибка получения товара {product_id}: {e}")
            return None

    async def get_products_catalog(
            self,
            filters: Optional[ProductFilterSchema] = None,
            include_hidden: bool = False
    ) -> Dict[str, Any]:
        """
        Получение каталога товаров с фильтрацией и пагинацией

        Args:
            filters: Фильтры для поиска
            include_hidden: Включать ли скрытые товары

        Returns:
            Dict с товарами и метаданными пагинации
        """
        try:
            # Базовый запрос
            query = select(Product)

            # Фильтры видимости
            if not include_hidden:
                query = query.where(Product.is_hidden == False)

            # Применяем фильтры
            if filters:
                # Фильтр по категории
                if filters.category:
                    query = query.where(Product.category == filters.category)

                # Фильтр по доступности
                if filters.is_available is not None:
                    query = query.where(Product.is_available == filters.is_available)

                # Фильтр по наличию
                if filters.in_stock is not None:
                    if filters.in_stock:
                        query = query.where(Product.stock_quantity > 0)
                    else:
                        query = query.where(Product.stock_quantity <= 0)

                # Фильтр по цене
                if filters.min_price is not None:
                    query = query.where(Product.price >= filters.min_price)
                if filters.max_price is not None:
                    query = query.where(Product.price <= filters.max_price)

                # Поиск по названию
                if filters.search:
                    search_pattern = f"%{filters.search.lower()}%"
                    query = query.where(
                        or_(
                            func.lower(Product.name).like(search_pattern),
                            func.lower(Product.description).like(search_pattern),
                            func.lower(Product.tags).like(search_pattern)
                        )
                    )

            # Подсчет общего количества
            count_query = select(func.count(Product.id)).select_from(query.subquery())
            total_result = await self.session.execute(count_query)
            total = total_result.scalar()

            # Сортировка
            if filters and filters.sort_by:
                if hasattr(Product, filters.sort_by):
                    sort_column = getattr(Product, filters.sort_by)
                    if filters.sort_desc:
                        query = query.order_by(sort_column.desc())
                    else:
                        query = query.order_by(sort_column)
                else:
                    # По умолчанию сортировка
                    query = query.order_by(Product.sort_order, Product.created_at.desc())
            else:
                query = query.order_by(Product.sort_order, Product.created_at.desc())

            # Пагинация
            if filters:
                offset = (filters.page - 1) * filters.per_page
                query = query.offset(offset).limit(filters.per_page)

            # Выполняем запрос
            result = await self.session.execute(query)
            products = result.scalars().all()

            # Метаданные пагинации
            pagination = {}
            if filters:
                total_pages = (total + filters.per_page - 1) // filters.per_page
                pagination = {
                    "page": filters.page,
                    "per_page": filters.per_page,
                    "total": total,
                    "total_pages": total_pages,
                    "has_next": filters.page < total_pages,
                    "has_prev": filters.page > 1
                }

            logger.info(f"📦 Получено товаров: {len(products)} из {total}")

            return {
                "products": products,
                "pagination": pagination,
                "total": total
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения каталога: {e}")
            return {"products": [], "pagination": {}, "total": 0}

    async def create_product(self, product_data: ProductCreateSchema) -> Optional[Product]:
        """
        Создание нового товара

        Args:
            product_data: Данные для создания товара

        Returns:
            Созданный товар или None
        """
        try:
            # Создаем товар
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

    async def update_product(
            self,
            product_id: int,
            product_data: ProductUpdateSchema
    ) -> Optional[Product]:
        """
        Обновление товара

        Args:
            product_id: ID товара
            product_data: Данные для обновления

        Returns:
            Обновленный товар или None
        """
        try:
            # Получаем товар
            product = await self.get_product_by_id(product_id)
            if not product:
                logger.warning(f"⚠️ Товар {product_id} не найден")
                return None

            # Сохраняем старый остаток для проверки
            old_stock = product.stock_quantity

            # Обновляем поля
            update_data = product_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(product, field, value)

            await self.session.commit()
            await self.session.refresh(product)

            # Проверяем изменение остатка
            new_stock = product.stock_quantity
            if new_stock != old_stock:
                await self._check_low_stock_notification(product)

            logger.success(f"✅ Обновлен товар: {product.name} (ID: {product.id})")
            return product

        except Exception as e:
            logger.error(f"❌ Ошибка обновления товара {product_id}: {e}")
            await self.session.rollback()
            return None

    async def delete_product(self, product_id: int) -> bool:
        """
        Удаление товара

        Args:
            product_id: ID товара

        Returns:
            True если удален успешно
        """
        try:
            # Проверяем, что товар не используется в активных заказах
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
            product = await self.get_product_by_id(product_id)
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
            product = await self.get_product_by_id(product_id)
            if not product:
                logger.warning(f"⚠️ Товар {product_id} не найден для резервирования")
                return False

            if not product.can_order_quantity(quantity):
                logger.warning(f"⚠️ Недостаточно товара {product.name} для резервирования {quantity}")
                return False

            await product.update_stock(-quantity)
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
            product = await self.get_product_by_id(product_id)
            if not product:
                return False

            await product.update_stock(quantity)
            await self.session.commit()

            logger.info(f"📦 Восстановлено {quantity} шт. товара {product.name}")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка восстановления товара {product_id}: {e}")
            await self.session.rollback()
            return False

    async def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """
        Поиск товаров по названию и описанию

        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов

        Returns:
            Список найденных товаров
        """
        try:
            search_pattern = f"%{query.lower()}%"

            sql_query = select(Product).where(
                and_(
                    Product.is_available == True,
                    Product.is_hidden == False,
                    or_(
                        func.lower(Product.name).like(search_pattern),
                        func.lower(Product.description).like(search_pattern),
                        func.lower(Product.tags).like(search_pattern)
                    )
                )
            ).order_by(Product.sort_order).limit(limit)

            result = await self.session.execute(sql_query)
            products = result.scalars().all()

            logger.info(f"🔍 Найдено товаров по запросу '{query}': {len(products)}")
            return products

        except Exception as e:
            logger.error(f"❌ Ошибка поиска товаров: {e}")
            return []

    async def get_categories(self) -> List[str]:
        """
        Получение списка всех категорий товаров

        Returns:
            Список уникальных категорий
        """
        try:
            query = select(Product.category).where(
                and_(
                    Product.category.isnot(None),
                    Product.is_hidden == False
                )
            ).distinct()

            result = await self.session.execute(query)
            categories = [cat for cat in result.scalars().all() if cat]

            logger.info(f"📂 Найдено категорий: {len(categories)}")
            return categories

        except Exception as e:
            logger.error(f"❌ Ошибка получения категорий: {e}")
            return []

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

    async def save_product_image(self, product_id: int, image_data: bytes, filename: str) -> Optional[str]:
        """
        Сохранение изображения товара

        Args:
            product_id: ID товара
            image_data: Данные изображения
            filename: Имя файла

        Returns:
            Путь к сохраненному файлу или None
        """
        try:
            # Создаем директорию если не существует
            upload_dir = os.path.join(marketplace_settings.UPLOAD_PATH, "products")
            os.makedirs(upload_dir, exist_ok=True)

            # Генерируем имя файла
            file_extension = os.path.splitext(filename)[1]
            new_filename = f"product_{product_id}_{hash(filename)}{file_extension}"
            file_path = os.path.join(upload_dir, new_filename)

            # Сохраняем файл
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(image_data)

            # Обновляем путь в базе данных
            relative_path = f"products/{new_filename}"
            await self.update_product(product_id, ProductUpdateSchema(image_path=relative_path))

            logger.success(f"✅ Сохранено изображение товара {product_id}: {relative_path}")
            return relative_path

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения изображения товара {product_id}: {e}")
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

    async def get_product_stats(self, product_id: int) -> Dict[str, Any]:
        """
        Получение статистики товара

        Args:
            product_id: ID товара

        Returns:
            Словарь со статистикой
        """
        try:
            product = await self.get_product_by_id(product_id)
            if not product:
                return {}

            # TODO: Добавить запросы для получения статистики заказов
            # total_ordered_quantity = ...
            # revenue = ...
            # last_ordered = ...

            return {
                "views_count": product.views_count,
                "orders_count": product.orders_count,
                "total_ordered_quantity": 0,  # TODO
                "revenue": Decimal('0.00'),  # TODO
                "last_ordered": None,  # TODO
                "current_stock": product.stock_quantity,
                "is_low_stock": product.is_low_stock
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики товара {product_id}: {e}")
            return {}