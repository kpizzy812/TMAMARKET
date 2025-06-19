"""
Главный сервис для работы с товарами
Композитный сервис, объединяющий специализированные модульные сервисы
"""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.product import Product
from app.schemas.product import (
    ProductCreateSchema,
    ProductUpdateSchema,
    ProductFilterSchema
)
from app.services.product import (
    ProductCRUDService,
    ProductCatalogService,
    ProductStockService,
    ProductImageService
)


class ProductService:
    """
    Главный сервис для работы с товарами
    Объединяет функциональность всех специализированных сервисов
    """

    def __init__(self, session: AsyncSession):
        self.session = session

        # Инициализируем модульные сервисы
        self.crud = ProductCRUDService(session)
        self.catalog = ProductCatalogService(session)
        self.stock = ProductStockService(session)
        self.images = ProductImageService(session)

    # === CRUD операции (делегируем в ProductCRUDService) ===

    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Получение товара по ID"""
        return await self.crud.get_by_id(product_id, increment_views=True)

    async def create_product(self, product_data: ProductCreateSchema) -> Optional[Product]:
        """Создание нового товара"""
        return await self.crud.create(product_data)

    async def update_product(
        self,
        product_id: int,
        product_data: ProductUpdateSchema
    ) -> Optional[Product]:
        """Обновление товара"""
        return await self.crud.update(product_id, product_data)

    async def delete_product(self, product_id: int) -> bool:
        """Удаление товара"""
        return await self.crud.delete(product_id)

    async def get_product_stats(self, product_id: int) -> Dict[str, Any]:
        """Получение статистики товара"""
        return await self.crud.get_stats(product_id)

    # === Каталог и поиск (делегируем в ProductCatalogService) ===

    async def get_products_catalog(
        self,
        filters: Optional[ProductFilterSchema] = None,
        include_hidden: bool = False
    ) -> Dict[str, Any]:
        """Получение каталога товаров с фильтрацией и пагинацией"""
        return await self.catalog.get_catalog(filters, include_hidden)

    async def search_products(self, query: str, limit: int = 10) -> List[Product]:
        """Поиск товаров по названию и описанию"""
        return await self.catalog.search_products(query, limit)

    async def get_categories(self) -> List[str]:
        """Получение списка всех категорий товаров"""
        return await self.catalog.get_categories()

    async def get_products_by_category(self, category: str, limit: int = 20) -> List[Product]:
        """Получение товаров по категории"""
        return await self.catalog.get_products_by_category(category, limit)

    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        """Получение рекомендуемых товаров"""
        return await self.catalog.get_featured_products(limit)

    # === Управление остатками (делегируем в ProductStockService) ===

    async def update_stock(self, product_id: int, new_quantity: int) -> bool:
        """Обновление остатка товара"""
        return await self.stock.update_stock(product_id, new_quantity)

    async def reserve_stock(self, product_id: int, quantity: int) -> bool:
        """Резервирование товара (уменьшение остатка)"""
        return await self.stock.reserve_stock(product_id, quantity)

    async def restore_stock(self, product_id: int, quantity: int) -> bool:
        """Восстановление товара (увеличение остатка)"""
        return await self.stock.restore_stock(product_id, quantity)

    async def bulk_reserve_stock(self, items: List[dict]) -> bool:
        """Массовое резервирование товаров"""
        return await self.stock.bulk_reserve_stock(items)

    async def bulk_restore_stock(self, items: List[dict]) -> bool:
        """Массовое восстановление товаров"""
        return await self.stock.bulk_restore_stock(items)

    async def get_low_stock_products(self, threshold: Optional[int] = None) -> List[Product]:
        """Получение товаров с низким остатком"""
        return await self.stock.get_low_stock_products(threshold)

    async def check_product_availability(self, product_id: int, quantity: int) -> dict:
        """Проверка доступности товара для заказа"""
        return await self.stock.check_product_availability(product_id, quantity)

    async def get_stock_movements_summary(self, product_id: int) -> dict:
        """Получение сводки движения остатков товара"""
        return await self.stock.get_stock_movements_summary(product_id)

    # === Работа с изображениями (делегируем в ProductImageService) ===

    async def save_product_image(
        self,
        product_id: int,
        image_data: bytes,
        filename: str,
        optimize: bool = True
    ) -> Optional[str]:
        """Сохранение изображения товара"""
        return await self.images.save_product_image(product_id, image_data, filename, optimize)

    async def delete_product_image(self, product_id: int) -> bool:
        """Удаление изображения товара"""
        return await self.images.delete_product_image(product_id)

    async def get_image_info(self, product_id: int) -> Optional[dict]:
        """Получение информации об изображении товара"""
        return await self.images.get_image_info(product_id)

    # === Дополнительные удобные методы ===

    async def get_product_for_order(self, product_id: int, quantity: int) -> Optional[dict]:
        """
        Получение товара для добавления в заказ с проверкой доступности

        Args:
            product_id: ID товара
            quantity: Желаемое количество

        Returns:
            Словарь с информацией о товаре или None
        """
        try:
            # Получаем товар
            product = await self.get_product_by_id(product_id)
            if not product:
                return None

            # Проверяем доступность
            availability = await self.check_product_availability(product_id, quantity)

            return {
                "product": product,
                "availability": availability,
                "requested_quantity": quantity,
                "total_price": product.price * quantity
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения товара для заказа {product_id}: {e}")
            return None

    async def validate_order_items(self, items: List[dict]) -> dict:
        """
        Валидация списка товаров для заказа

        Args:
            items: Список словарей {"product_id": int, "quantity": int}

        Returns:
            Словарь с результатом валидации
        """
        try:
            valid_items = []
            invalid_items = []
            total_amount = Decimal('0.00')

            for item in items:
                product_id = item.get("product_id")
                quantity = item.get("quantity", 1)

                product_info = await self.get_product_for_order(product_id, quantity)

                if product_info and product_info["availability"]["available"]:
                    valid_items.append({
                        "product_id": product_id,
                        "product": product_info["product"],
                        "quantity": quantity,
                        "price": product_info["product"].price,
                        "total_price": product_info["total_price"]
                    })
                    total_amount += product_info["total_price"]
                else:
                    invalid_items.append({
                        "product_id": product_id,
                        "quantity": quantity,
                        "reason": product_info["availability"]["reason"] if product_info else "Товар не найден"
                    })

            return {
                "valid": len(invalid_items) == 0,
                "valid_items": valid_items,
                "invalid_items": invalid_items,
                "total_amount": total_amount,
                "total_items": len(valid_items)
            }

        except Exception as e:
            logger.error(f"❌ Ошибка валидации товаров для заказа: {e}")
            return {
                "valid": False,
                "valid_items": [],
                "invalid_items": items,
                "total_amount": Decimal('0.00'),
                "total_items": 0
            }

    async def get_product_summary(self, product_id: int) -> Optional[dict]:
        """
        Получение полной сводки по товару

        Args:
            product_id: ID товара

        Returns:
            Словарь с полной информацией о товаре
        """
        try:
            # Получаем основную информацию
            product = await self.get_product_by_id(product_id)
            if not product:
                return None

            # Получаем дополнительную информацию
            stats = await self.get_product_stats(product_id)
            stock_summary = await self.get_stock_movements_summary(product_id)
            image_info = await self.get_image_info(product_id)

            return {
                "product": product,
                "stats": stats,
                "stock": stock_summary,
                "images": image_info
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения сводки товара {product_id}: {e}")
            return None