"""
Модели промокодов
Система скидок и промоакций
"""

import enum
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import (
    String, Text, Boolean, DateTime, Integer,
    Numeric, ForeignKey, func, Index, Enum, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PromocodeStatus(enum.Enum):
    """Статусы промокода"""
    ACTIVE = "active"  # Активен
    INACTIVE = "inactive"  # Неактивен
    EXPIRED = "expired"  # Истек
    EXHAUSTED = "exhausted"  # Исчерпан (закончились активации)


class Promocode(Base):
    """Модель промокода"""

    __tablename__ = "promocodes"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="Код промокода (например, SUMMER20)"
    )

    name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Название промокода для админки"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Описание промокода"
    )

    # Настройки скидки
    discount_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Процент скидки (1-100)"
    )

    min_order_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Минимальная сумма заказа для применения"
    )

    max_discount_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Максимальная сумма скидки"
    )

    # Лимиты использования
    max_uses: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Максимальное количество активаций (NULL = без лимита)"
    )

    current_uses: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Текущее количество использований"
    )

    one_per_user: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Только один раз на пользователя"
    )

    # Временные ограничения
    valid_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Действует с даты"
    )

    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Действует до даты"
    )

    # Статус и управление
    status: Mapped[PromocodeStatus] = mapped_column(
        Enum(PromocodeStatus),
        default=PromocodeStatus.ACTIVE,
        index=True,
        comment="Статус промокода"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Активен ли промокод"
    )

    # Служебная информация
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Заметки администратора"
    )

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID администратора, создавшего промокод"
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления"
    )

    # Связи
    usages: Mapped[List["PromocodeUsage"]] = relationship(
        "PromocodeUsage",
        back_populates="promocode",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    orders: Mapped[List["Order"]] = relationship(
        "Order",
        back_populates="promocode",
        lazy="selectin"
    )

    creator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[created_by],
        lazy="selectin"
    )

    # Индексы
    __table_args__ = (
        Index("idx_promocode_code_active", "code", "is_active"),
        Index("idx_promocode_status", "status"),
        Index("idx_promocode_valid_dates", "valid_from", "valid_until"),
    )

    def __repr__(self) -> str:
        return f"<Promocode(id={self.id}, code={self.code}, discount={self.discount_percent}%)>"

    @property
    def remaining_uses(self) -> Optional[int]:
        """Возвращает оставшееся количество использований"""
        if self.max_uses is None:
            return None
        return max(0, self.max_uses - self.current_uses)

    @property
    def is_exhausted(self) -> bool:
        """Проверяет, исчерпаны ли использования"""
        if self.max_uses is None:
            return False
        return self.current_uses >= self.max_uses

    @property
    def is_time_valid(self) -> bool:
        """Проверяет, действует ли промокод по времени"""
        now = datetime.now()

        if self.valid_from and now < self.valid_from:
            return False

        if self.valid_until and now > self.valid_until:
            return False

        return True

    @property
    def is_valid(self) -> bool:
        """Проверяет общую валидность промокода"""
        return (
                self.is_active
                and self.status == PromocodeStatus.ACTIVE
                and not self.is_exhausted
                and self.is_time_valid
        )

    @property
    def status_display(self) -> str:
        """Возвращает человекочитаемый статус"""
        if not self.is_active:
            return "Отключен"

        if self.is_exhausted:
            return "Исчерпан"

        if not self.is_time_valid:
            return "Истек"

        status_map = {
            PromocodeStatus.ACTIVE: "Активен",
            PromocodeStatus.INACTIVE: "Неактивен",
            PromocodeStatus.EXPIRED: "Истек",
            PromocodeStatus.EXHAUSTED: "Исчерпан"
        }
        return status_map.get(self.status, self.status.value)

    def can_be_used_by_user(self, user_id: int) -> bool:
        """
        Проверяет, может ли пользователь использовать промокод

        Args:
            user_id: ID пользователя

        Returns:
            bool: Может ли использовать
        """
        if not self.is_valid:
            return False

        if self.one_per_user:
            # Проверяем, использовал ли уже этот пользователь промокод
            for usage in self.usages:
                if usage.user_id == user_id:
                    return False

        return True

    def can_be_applied_to_order(self, order_amount: Decimal) -> bool:
        """
        Проверяет, можно ли применить промокод к заказу

        Args:
            order_amount: Сумма заказа

        Returns:
            bool: Можно ли применить
        """
        if not self.is_valid:
            return False

        if self.min_order_amount and order_amount < self.min_order_amount:
            return False

        return True

    def calculate_discount(self, order_amount: Decimal) -> Decimal:
        """
        Рассчитывает размер скидки для заказа

        Args:
            order_amount: Сумма заказа

        Returns:
            Decimal: Размер скидки
        """
        if not self.can_be_applied_to_order(order_amount):
            return Decimal('0.00')

        discount_amount = order_amount * (Decimal(self.discount_percent) / 100)

        if self.max_discount_amount:
            discount_amount = min(discount_amount, self.max_discount_amount)

        return discount_amount

    def use(self, user_id: int, order_id: Optional[int] = None) -> "PromocodeUsage":
        """
        Использует промокод

        Args:
            user_id: ID пользователя
            order_id: ID заказа (опционально)

        Returns:
            PromocodeUsage: Запись об использовании

        Raises:
            ValueError: Если промокод нельзя использовать
        """
        if not self.can_be_used_by_user(user_id):
            raise ValueError("Промокод нельзя использовать")

        # Увеличиваем счетчик использований
        self.current_uses += 1

        # Обновляем статус если исчерпан
        if self.is_exhausted:
            self.status = PromocodeStatus.EXHAUSTED

        # Создаем запись об использовании
        usage = PromocodeUsage(
            promocode_id=self.id,
            user_id=user_id,
            order_id=order_id
        )

        return usage

    def update_status(self) -> None:
        """Обновляет статус промокода на основе текущих условий"""
        if not self.is_active:
            self.status = PromocodeStatus.INACTIVE
        elif self.is_exhausted:
            self.status = PromocodeStatus.EXHAUSTED
        elif not self.is_time_valid:
            self.status = PromocodeStatus.EXPIRED
        else:
            self.status = PromocodeStatus.ACTIVE


class PromocodeUsage(Base):
    """Модель использования промокода"""

    __tablename__ = "promocode_usages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Связи
    promocode_id: Mapped[int] = mapped_column(
        ForeignKey("promocodes.id", ondelete="CASCADE"),
        index=True,
        comment="ID промокода"
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="ID пользователя"
    )

    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="ID заказа (если применен к заказу)"
    )

    # Информация об использовании
    discount_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Размер скидки"
    )

    order_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Сумма заказа на момент применения"
    )

    # Временная метка
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата и время использования"
    )

    # Связи
    promocode: Mapped["Promocode"] = relationship(
        "Promocode",
        back_populates="usages"
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="promocode_usages"
    )

    order: Mapped[Optional["Order"]] = relationship(
        "Order",
        lazy="selectin"
    )

    # Ограничения
    __table_args__ = (
        UniqueConstraint("promocode_id", "user_id", name="uq_promocode_user"),
        Index("idx_promocode_usage_date", "used_at"),
    )

    def __repr__(self) -> str:
        return f"<PromocodeUsage(id={self.id}, promocode_id={self.promocode_id}, user_id={self.user_id})>"