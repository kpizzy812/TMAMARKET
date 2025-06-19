"""
Authentication dependencies
Зависимости для аутентификации пользователей
"""

from typing import Optional, Union
from fastapi import Depends, HTTPException, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.api.dependencies.database import get_database_session
from app.models.user import User
from app.core.config import telegram_settings


class TelegramAuth:
    """Класс для аутентификации через Telegram"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Получение пользователя по Telegram ID

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            User или None
        """
        try:
            query = select(User).where(User.telegram_id == telegram_id)
            result = await self.session.execute(query)
            user = result.scalar_one_or_none()

            if user:
                # Обновляем время последней активности
                from datetime import datetime
                user.last_activity = datetime.now()
                await self.session.commit()

            return user

        except Exception as e:
            logger.error(f"❌ Ошибка получения пользователя {telegram_id}: {e}")
            return None

    async def create_user_from_telegram(self, telegram_data: dict) -> User:
        """
        Создание пользователя из данных Telegram

        Args:
            telegram_data: Данные пользователя из Telegram

        Returns:
            User: Созданный пользователь
        """
        try:
            user = User(
                telegram_id=telegram_data.get("id"),
                username=telegram_data.get("username"),
                first_name=telegram_data.get("first_name"),
                last_name=telegram_data.get("last_name"),
                language_code=telegram_data.get("language_code")
            )

            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

            logger.info(f"👤 Создан новый пользователь: {user.telegram_id}")
            return user

        except Exception as e:
            logger.error(f"❌ Ошибка создания пользователя: {e}")
            await self.session.rollback()
            raise

    async def get_or_create_user(self, telegram_data: dict) -> User:
        """
        Получение или создание пользователя

        Args:
            telegram_data: Данные из Telegram

        Returns:
            User: Пользователь
        """
        telegram_id = telegram_data.get("id")
        if not telegram_id:
            raise ValueError("Отсутствует telegram_id")

        # Пытаемся найти существующего пользователя
        user = await self.get_user_by_telegram_id(telegram_id)

        if not user:
            # Создаем нового пользователя
            user = await self.create_user_from_telegram(telegram_data)

        return user


async def get_telegram_auth(
        session: AsyncSession = Depends(get_database_session)
) -> TelegramAuth:
    """
    Dependency для получения TelegramAuth

    Args:
        session: Сессия БД

    Returns:
        TelegramAuth: Экземпляр для аутентификации
    """
    return TelegramAuth(session)


async def get_current_user(
        x_telegram_user: Optional[str] = Header(None, alias="X-Telegram-User"),
        telegram_id: Optional[int] = Query(None, alias="user_id"),
        auth: TelegramAuth = Depends(get_telegram_auth)
) -> User:
    """
    Dependency для получения текущего пользователя

    Args:
        x_telegram_user: Данные пользователя в заголовке (JSON)
        telegram_id: ID пользователя в query параметрах
        auth: Сервис аутентификации

    Returns:
        User: Текущий пользователь

    Raises:
        HTTPException: Если пользователь не найден
    """
    user = None

    # Пытаемся получить пользователя из заголовка
    if x_telegram_user:
        try:
            import json
            telegram_data = json.loads(x_telegram_user)
            user = await auth.get_or_create_user(telegram_data)
            logger.debug(f"👤 Пользователь из заголовка: {user.telegram_id}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка парсинга заголовка: {e}")

    # Если не получилось, пытаемся по telegram_id
    if not user and telegram_id:
        user = await auth.get_user_by_telegram_id(telegram_id)
        logger.debug(f"👤 Пользователь по ID: {telegram_id}")

    if not user:
        logger.warning("🚫 Пользователь не аутентифицирован")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не аутентифицирован"
        )

    if not user.is_active:
        logger.warning(f"🚫 Пользователь {user.telegram_id} заблокирован")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь заблокирован"
        )

    return user


async def get_current_user_optional(
        x_telegram_user: Optional[str] = Header(None, alias="X-Telegram-User"),
        telegram_id: Optional[int] = Query(None, alias="user_id"),
        auth: TelegramAuth = Depends(get_telegram_auth)
) -> Optional[User]:
    """
    Dependency для получения текущего пользователя (опционально)

    Args:
        x_telegram_user: Данные пользователя в заголовке
        telegram_id: ID пользователя в query параметрах
        auth: Сервис аутентификации

    Returns:
        User или None
    """
    try:
        return await get_current_user(x_telegram_user, telegram_id, auth)
    except HTTPException:
        return None


async def get_admin_user(
        current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency для получения пользователя-администратора

    Args:
        current_user: Текущий пользователь

    Returns:
        User: Пользователь-администратор

    Raises:
        HTTPException: Если пользователь не администратор
    """
    if not current_user.is_admin:
        logger.warning(f"🚫 Пользователь {current_user.telegram_id} не админ")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав доступа"
        )

    logger.debug(f"⚙️ Админ {current_user.telegram_id} аутентифицирован")
    return current_user


# Готовые dependencies для использования
CurrentUser = Depends(get_current_user)
CurrentUserOptional = Depends(get_current_user_optional)
AdminUser = Depends(get_admin_user)