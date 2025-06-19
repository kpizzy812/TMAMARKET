"""
Модель пользователя
Хранит данные пользователей Telegram и их заказов
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    BigInteger, String, Boolean, DateTime, Text,
    Integer, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class User(Base):
    """Модель пользователя Telegram"""

    __tablename__ = "users"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        comment="ID пользователя в Telegram"
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Username в Telegram (@username)"
    )
    first_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Имя пользователя в Telegram"
    )
    last_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Фамилия пользователя в Telegram"
    )

    # Контактная информация для заказов
    full_name: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="ФИО для заказов (заполняется при оформлении)"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Номер телефона для заказов"
    )

    # Статусы и роли
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Активен ли пользователь"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Является ли администратором"
    )
    is_blocked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Заблокирован ли пользователь"
    )

    # Настройки уведомлений
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Разрешены ли уведомления"
    )

    # Дополнительная информация
    language_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Код языка пользователя"
    )
    timezone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Часовой пояс пользователя"
    )

    # Служебная информация
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Заметки администратора о пользователе"
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата регистрации"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления"
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата последней активности"
    )

    # Связи с другими таблицами
    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="user",
        lazy="selectin"
    )

    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="user",
        lazy="selectin"
    )

    promocode_usages: Mapped[List["PromocodeUsage"]] = relationship(
        "PromocodeUsage",
        back_populates="user",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

    @property
    def display_name(self) -> str:
        """Возвращает отображаемое имя пользователя"""
        if self.full_name:
            return self.full_name

        parts = []
        if self.first_name:
            parts.append(self.first_name)
        if self.last_name:
            parts.append(self.last_name)

        if parts:
            return " ".join(parts)

        return self.username or f"User {self.telegram_id}"

    @property
    def is_new_user(self) -> bool:
        """Проверяет, является ли пользователь новым (без заказов)"""
        return len(self.orders) == 0

    @property
    def total_orders(self) -> int:
        """Возвращает количество заказов пользователя"""
        return len(self.orders)

    def has_contact_info(self) -> bool:
        """Проверяет, заполнена ли контактная информация"""
        return bool(self.full_name and self.phone)

    def can_receive_notifications(self) -> bool:
        """Проверяет, может ли пользователь получать уведомления"""
        return self.is_active and not self.is_blocked and self.notifications_enabled