"""
Утилиты для работы с сессиями базы данных
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from app.core.database import Base


class DatabaseManager:
    """Менеджер для общих операций с базой данных"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(
            self,
            model: type[Base],
            obj_id: int,
            relationships: Optional[List[str]] = None
    ) -> Optional[Base]:
        """
        Получение объекта по ID с возможностью загрузки связей

        Args:
            model: Модель SQLAlchemy
            obj_id: ID объекта
            relationships: Список связей для загрузки

        Returns:
            Объект модели или None
        """
        query = select(model).where(model.id == obj_id)

        if relationships:
            for rel in relationships:
                query = query.options(selectinload(getattr(model, rel)))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_multi(
            self,
            model: type[Base],
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict[str, Any]] = None,
            order_by: Optional[str] = None
    ) -> List[Base]:
        """
        Получение списка объектов с фильтрацией и пагинацией

        Args:
            model: Модель SQLAlchemy
            skip: Количество записей для пропуска
            limit: Максимальное количество записей
            filters: Словарь фильтров {поле: значение}
            order_by: Поле для сортировки

        Returns:
            Список объектов модели
        """
        query = select(model)

        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.where(getattr(model, field) == value)

        if order_by and hasattr(model, order_by):
            query = query.order_by(getattr(model, order_by))

        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, model: type[Base], **kwargs) -> Base:
        """
        Создание нового объекта

        Args:
            model: Модель SQLAlchemy
            **kwargs: Поля для создания объекта

        Returns:
            Созданный объект
        """
        obj = model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update_by_id(
            self,
            model: type[Base],
            obj_id: int,
            **kwargs
    ) -> Optional[Base]:
        """
        Обновление объекта по ID

        Args:
            model: Модель SQLAlchemy
            obj_id: ID объекта
            **kwargs: Поля для обновления

        Returns:
            Обновленный объект или None
        """
        query = (
            update(model)
            .where(model.id == obj_id)
            .values(**kwargs)
            .execution_options(synchronize_session="evaluate")
        )

        await self.session.execute(query)
        await self.session.commit()

        return await self.get_by_id(model, obj_id)

    async def delete_by_id(self, model: type[Base], obj_id: int) -> bool:
        """
        Удаление объекта по ID

        Args:
            model: Модель SQLAlchemy
            obj_id: ID объекта

        Returns:
            True если объект был удален, False если не найден
        """
        query = delete(model).where(model.id == obj_id)
        result = await self.session.execute(query)
        await self.session.commit()

        return result.rowcount > 0

    async def count(
            self,
            model: type[Base],
            filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Подсчет количества записей

        Args:
            model: Модель SQLAlchemy
            filters: Словарь фильтров

        Returns:
            Количество записей
        """
        query = select(func.count(model.id))

        if filters:
            for field, value in filters.items():
                if hasattr(model, field):
                    query = query.where(getattr(model, field) == value)

        result = await self.session.execute(query)
        return result.scalar()

    async def exists(
            self,
            model: type[Base],
            filters: Dict[str, Any]
    ) -> bool:
        """
        Проверка существования записи

        Args:
            model: Модель SQLAlchemy
            filters: Словарь фильтров

        Returns:
            True если запись существует
        """
        query = select(model)

        for field, value in filters.items():
            if hasattr(model, field):
                query = query.where(getattr(model, field) == value)

        query = query.limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() is not None