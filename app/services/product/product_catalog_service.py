"""
Сервис каталога товаров
Поиск, фильтрация, пагинация, категории
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from loguru import logger

from app.models.product import Product
from app.schemas.product import ProductFilterSchema


class ProductCatalogService:
    """Сервис для работы с каталогом товаров"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_catalog(
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
            query = self._apply_filters(query, filters)

            # Подсчет общего количества
            total = await self._count_total(query)

            # Сортировка
            query = self._apply_sorting(query, filters)

            # Пагинация
            if filters:
                offset = (filters.page - 1) * filters.per_page
                query = query.offset(offset).limit(filters.per_page)

            # Выполняем запрос
            result = await self.session.execute(query)
            products = result.scalars().all()

            # Метаданные пагинации
            pagination = self._build_pagination(filters, total)

            logger.info(f"📦 Получено товаров: {len(products)} из {total}")

            return {
                "products": products,
                "pagination": pagination,
                "total": total
            }

        except Exception as e:
            logger.error(f"❌ Ошибка получения каталога: {e}")
            return {"products": [], "pagination": {}, "total": 0}

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

    async def get_products_by_category(self, category: str, limit: int = 20) -> List[Product]:
        """
        Получение товаров по категории

        Args:
            category: Название категории
            limit: Максимальное количество товаров

        Returns:
            Список товаров категории
        """
        try:
            query = select(Product).where(
                and_(
                    Product.category == category,
                    Product.is_available == True,
                    Product.is_hidden == False
                )
            ).order_by(Product.sort_order).limit(limit)

            result = await self.session.execute(query)
            products = result.scalars().all()

            logger.info(f"📂 Товаров в категории '{category}': {len(products)}")
            return products

        except Exception as e:
            logger.error(f"❌ Ошибка получения товаров категории {category}: {e}")
            return []

    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        """
        Получение рекомендуемых товаров

        Args:
            limit: Максимальное количество товаров

        Returns:
            Список рекомендуемых товаров
        """
        try:
            # Сортируем по популярности (просмотры + заказы)
            query = select(Product).where(
                and_(
                    Product.is_available == True,
                    Product.is_hidden == False,
                    Product.stock_quantity > 0
                )
            ).order_by(
                (Product.views_count + Product.orders_count * 10).desc(),
                Product.created_at.desc()
            ).limit(limit)

            result = await self.session.execute(query)
            products = result.scalars().all()

            logger.info(f"⭐ Рекомендуемых товаров: {len(products)}")
            return products

        except Exception as e:
            logger.error(f"❌ Ошибка получения рекомендуемых товаров: {e}")
            return []

    def _apply_filters(self, query, filters: Optional[ProductFilterSchema]):
        """Применение фильтров к запросу"""
        if not filters:
            return query

        # Фильтр по категории
        if filters.category:
            query = query.where(Product.category == filters.category)

        # Фильтр по доступности
        if filters.is_available is not None:
            query = query.where(Product.is_available == filters.is_available)

        # Фильтр по видимости
        if filters.is_hidden is not None:
            query = query.where(Product.is_hidden == filters.is_hidden)

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

        return query

    def _apply_sorting(self, query, filters: Optional[ProductFilterSchema]):
        """Применение сортировки к запросу"""
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

        return query

    async def _count_total(self, query) -> int:
        """Подсчет общего количества товаров"""
        try:
            count_query = select(func.count(Product.id)).select_from(query.subquery())
            total_result = await self.session.execute(count_query)
            return total_result.scalar()
        except Exception as e:
            logger.error(f"❌ Ошибка подсчета товаров: {e}")
            return 0

    def _build_pagination(self, filters: Optional[ProductFilterSchema], total: int) -> Dict[str, Any]:
        """Построение метаданных пагинации"""
        if not filters:
            return {}

        total_pages = (total + filters.per_page - 1) // filters.per_page
        return {
            "page": filters.page,
            "per_page": filters.per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": filters.page < total_pages,
            "has_prev": filters.page > 1
        }