"""
Модель платежей
Обработка USDT и СБП платежей
"""

import enum
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal
from sqlalchemy import (
    String, Text, Boolean, DateTime, Integer,
    Numeric, ForeignKey, func, Index, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PaymentMethod(enum.Enum):
    """Способы оплаты"""
    USDT_TRC20 = "usdt_trc20"
    USDT_BEP20 = "usdt_bep20"
    USDT_TON = "usdt_ton"
    SBP = "sbp"


class PaymentStatus(enum.Enum):
    """Статусы платежа"""
    PENDING = "pending"  # Ожидает оплаты
    PROCESSING = "processing"  # Обрабатывается
    CHECKING = "checking"  # Проверяется поступление
    COMPLETED = "completed"  # Завершен успешно
    FAILED = "failed"  # Неуспешен
    CANCELLED = "cancelled"  # Отменен
    EXPIRED = "expired"  # Истек по времени
    REFUNDED = "refunded"  # Возвращен


class BlockchainNetwork(enum.Enum):
    """Блокчейн сети"""
    TRON = "tron"
    BSC = "bsc"
    TON = "ton"


class Payment(Base):
    """Модель платежа"""

    __tablename__ = "payments"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    payment_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        comment="Уникальный ID платежа"
    )

    # Связь с заказом
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        comment="ID заказа"
    )

    # Связь с пользователем
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="ID пользователя"
    )

    # Способ оплаты и статус
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod),
        nullable=False,
        comment="Способ оплаты"
    )

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        index=True,
        comment="Статус платежа"
    )

    # Суммы
    amount_rub: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Сумма в рублях"
    )

    amount_crypto: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        comment="Сумма в криптовалюте"
    )

    # Уникальная сумма для идентификации USDT платежей
    unique_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        unique=True,
        comment="Уникальная сумма для автоопределения платежа"
    )

    # Курс обмена на момент создания платежа
    exchange_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 4),
        nullable=True,
        comment="Курс RUB/USDT на момент создания"
    )

    # USDT платежи
    wallet_address: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Адрес кошелька для оплаты"
    )

    blockchain_network: Mapped[Optional[BlockchainNetwork]] = mapped_column(
        Enum(BlockchainNetwork),
        nullable=True,
        comment="Блокчейн сеть"
    )

    transaction_hash: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        index=True,
        comment="Хеш транзакции"
    )

    from_address: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Адрес отправителя"
    )

    # СБП платежи
    sbp_order_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="ID заказа в системе СБП"
    )

    sbp_qr_code: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="QR код для оплаты СБП"
    )

    sbp_payment_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Ссылка для оплаты СБП"
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания платежа"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата обновления"
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Время истечения платежа"
    )

    confirmed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время подтверждения платежа"
    )

    # Дополнительные данные
    provider_data: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Дополнительные данные от провайдера (JSON)"
    )

    failure_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Причина неуспешного платежа"
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Заметки к платежу"
    )

    # Счетчики проверок (для USDT)
    check_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Количество попыток проверки платежа"
    )

    last_check_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время последней проверки"
    )

    # Связи
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="payment",
        lazy="selectin"
    )

    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin"
    )

    # Индексы
    __table_args__ = (
        Index("idx_payment_status_method", "status", "payment_method"),
        Index("idx_payment_expires", "expires_at"),
        Index("idx_payment_unique_amount", "unique_amount"),
        Index("idx_payment_tx_hash", "transaction_hash"),
    )

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, payment_id={self.payment_id}, method={self.payment_method.value})>"

    @property
    def is_expired(self) -> bool:
        """Проверяет, истек ли платеж по времени"""
        return datetime.now() > self.expires_at

    @property
    def is_pending(self) -> bool:
        """Проверяет, ожидает ли платеж оплаты"""
        return self.status in [PaymentStatus.PENDING, PaymentStatus.PROCESSING, PaymentStatus.CHECKING]

    @property
    def is_completed(self) -> bool:
        """Проверяет, завершен ли платеж успешно"""
        return self.status == PaymentStatus.COMPLETED

    @property
    def is_crypto_payment(self) -> bool:
        """Проверяет, является ли платеж криптовалютным"""
        return self.payment_method in [
            PaymentMethod.USDT_TRC20,
            PaymentMethod.USDT_BEP20,
            PaymentMethod.USDT_TON
        ]

    @property
    def time_left(self) -> Optional[timedelta]:
        """Возвращает оставшееся время для оплаты"""
        if self.is_expired:
            return None
        return self.expires_at - datetime.now()

    @property
    def time_left_minutes(self) -> int:
        """Возвращает оставшееся время в минутах"""
        time_left = self.time_left
        if not time_left:
            return 0
        return max(0, int(time_left.total_seconds() // 60))

    @property
    def status_display(self) -> str:
        """Возвращает человекочитаемый статус платежа"""
        status_map = {
            PaymentStatus.PENDING: "Ожидает оплаты",
            PaymentStatus.PROCESSING: "Обрабатывается",
            PaymentStatus.CHECKING: "Проверяется",
            PaymentStatus.COMPLETED: "Оплачен",
            PaymentStatus.FAILED: "Неуспешен",
            PaymentStatus.CANCELLED: "Отменен",
            PaymentStatus.EXPIRED: "Истек",
            PaymentStatus.REFUNDED: "Возвращен"
        }
        return status_map.get(self.status, self.status.value)

    @property
    def method_display(self) -> str:
        """Возвращает человекочитаемый способ оплаты"""
        method_map = {
            PaymentMethod.USDT_TRC20: "USDT (TRC-20)",
            PaymentMethod.USDT_BEP20: "USDT (BEP-20)",
            PaymentMethod.USDT_TON: "USDT (TON)",
            PaymentMethod.SBP: "Система быстрых платежей"
        }
        return method_map.get(self.payment_method, self.payment_method.value)

    @property
    def blockchain_explorer_url(self) -> Optional[str]:
        """Возвращает ссылку на транзакцию в блокчейн эксплорере"""
        if not self.transaction_hash or not self.blockchain_network:
            return None

        explorer_urls = {
            BlockchainNetwork.TRON: f"https://tronscan.org/#/transaction/{self.transaction_hash}",
            BlockchainNetwork.BSC: f"https://bscscan.com/tx/{self.transaction_hash}",
            BlockchainNetwork.TON: f"https://tonscan.org/tx/{self.transaction_hash}"
        }

        return explorer_urls.get(self.blockchain_network)

    def generate_payment_id(self) -> str:
        """Генерирует уникальный ID платежа"""
        from datetime import datetime
        import secrets

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = secrets.token_hex(4).upper()
        return f"PAY-{timestamp}-{random_part}"

    def generate_unique_amount(self, base_amount: Decimal) -> Decimal:
        """
        Генерирует уникальную сумму для идентификации платежа

        Args:
            base_amount: Базовая сумма в USDT

        Returns:
            Decimal: Уникальная сумма
        """
        import random

        # Добавляем случайные копейки (0.01-0.99 USDT)
        random_cents = Decimal(random.randint(1, 99)) / 100
        return base_amount + random_cents

    def set_expiration(self, minutes: int = 30) -> None:
        """
        Устанавливает время истечения платежа

        Args:
            minutes: Количество минут до истечения
        """
        self.expires_at = datetime.now() + timedelta(minutes=minutes)

    def mark_as_completed(self, transaction_hash: Optional[str] = None) -> None:
        """
        Отмечает платеж как завершенный

        Args:
            transaction_hash: Хеш транзакции (для криптоплатежей)
        """
        self.status = PaymentStatus.COMPLETED
        self.confirmed_at = datetime.now()

        if transaction_hash:
            self.transaction_hash = transaction_hash

    def mark_as_failed(self, reason: Optional[str] = None) -> None:
        """
        Отмечает платеж как неуспешный

        Args:
            reason: Причина неуспеха
        """
        self.status = PaymentStatus.FAILED
        if reason:
            self.failure_reason = reason

    def mark_as_expired(self) -> None:
        """Отмечает платеж как истекший"""
        self.status = PaymentStatus.EXPIRED

    def increment_check_attempts(self) -> None:
        """Увеличивает счетчик попыток проверки"""
        self.check_attempts += 1
        self.last_check_at = datetime.now()

    def can_be_checked(self) -> bool:
        """Проверяет, можно ли проверять статус платежа"""
        return (
                self.is_pending
                and not self.is_expired
                and self.is_crypto_payment
        )

    def should_be_checked(self) -> bool:
        """Проверяет, нужно ли проверять платеж сейчас"""
        if not self.can_be_checked():
            return False

        # Проверяем не чаще чем раз в минуту
        if self.last_check_at:
            time_since_check = datetime.now() - self.last_check_at
            if time_since_check.total_seconds() < 60:
                return False

        return True