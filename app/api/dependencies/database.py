"""
Database dependencies
Зависимости для работы с базой данных
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db, AsyncSessionLocal
from app.db.session import DatabaseManager


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии базы данных

    Yields:
        AsyncSession: Асинхронная сессия SQLAlchemy
    """
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("📊 Создана сессия БД")
            yield session
        except Exception as e:
            logger.error(f"❌ Ошибка сессии БД: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
            logger.debug("📊 Сессия БД закрыта")


async def get_db_manager(
        session: AsyncSession = Depends(get_database_session)
) -> DatabaseManager:
    """
    Dependency для получения менеджера базы данных

    Args:
        session: Сессия БД

    Returns:
        DatabaseManager: Менеджер для операций с БД
    """
    return DatabaseManager(session)


class DatabaseDependency:
    """Класс для dependency injection операций с БД"""

    def __init__(self, session: AsyncSession = Depends(get_database_session)):
        self.session = session
        self.manager = DatabaseManager(session)

    async def commit(self) -> None:
        """Сохранение изменений в БД"""
        try:
            await self.session.commit()
            logger.debug("✅ Изменения сохранены в БД")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения в БД: {e}")
            await self.session.rollback()
            raise

    async def rollback(self) -> None:
        """Откат изменений в БД"""
        await self.session.rollback()
        logger.debug("↩️ Изменения отменены")

    async def refresh(self, instance) -> None:
        """Обновление объекта из БД"""
        await self.session.refresh(instance)
        logger.debug(f"🔄 Объект {type(instance).__name__} обновлен")


# Готовые dependencies для использования в эндпоинтах
GetDB = Depends(get_database_session)
GetDBManager = Depends(get_db_manager)