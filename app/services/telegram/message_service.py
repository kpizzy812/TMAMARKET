"""
Сервис для отправки сообщений в Telegram
Пока заглушка, полная реализация будет позже
"""

from loguru import logger


class MessageService:
    """Сервис для отправки сообщений в Telegram"""

    def __init__(self):
        pass

    async def send_admin_notification(self, message: str) -> bool:
        """
        Отправка уведомления админу

        Args:
            message: Текст сообщения

        Returns:
            True если отправлено успешно
        """
        # TODO: Реализовать отправку через aiogram
        logger.info(f"📱 [STUB] Админ уведомление: {message}")
        return True

    async def send_user_message(self, user_id: int, message: str) -> bool:
        """
        Отправка сообщения пользователю

        Args:
            user_id: ID пользователя
            message: Текст сообщения

        Returns:
            True если отправлено успешно
        """
        # TODO: Реализовать отправку через aiogram
        logger.info(f"📱 [STUB] Сообщение пользователю {user_id}: {message}")
        return True