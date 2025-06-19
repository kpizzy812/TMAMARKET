"""
Модели заказа
Хранит информацию о заказах пользователей
"""

import enum
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import (
    String, Text, Boolean, DateTime, Integer,
    Numeric, ForeignKey, func, Index, Enum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class OrderStatus(enum.Enum):
    """Статусы заказа"""
    PENDING_PAYMENT = "pending_payment"  # Ожидает оплаты
    PAYMENT_PROCESSING = "payment_processing"  # Обработка платежа
    PAID = "paid"  # Оплачен
    CONFIRMED = "confirmed"  # Подтвержден
    ASSEMBLING = "assembling"  # Собирается
    SHIPPED = "shipped"  # Отправлен
    DELIVERED = "delivered"  # Доставлен
    CANCELLED = "cancelled"  # Отменен
    RETURNED = "returned"  # Возврат


class PaymentMethod(enum.Enum):
    """Способы оплаты"""
    USDT_TRC20 = "usdt_trc20"
    USDT_BEP20 = "usdt_bep20"
    USDT_TON = "usdt_ton"
    SBP = "sbp"


class PaymentStatus(enum.Enum):
    """Статусы оплаты"""
    PENDING = "pending"  # Ожидает
    PROCESSING = "processing"  # Обрабатывается
    COMPLETED = "completed"  # Завершена
    FAILED = "failed"  # Неуспешна
    CANCELLED = "cancelled"  # Отменена
    REFUNDED = "refunded"  # Возврат


class Order(Base):
    """Модель заказа"""

    __tablename__ = "orders"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        comment="Уникальный номер заказа"
    )

    # Связь с пользователем
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="ID пользователя"
    )

    # Статусы
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING_PAYMENT,
        index=True,
        comment="Статус заказа"
    )

    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        index=True,
        comment="Статус оплаты"
    )

    # Контактная информация заказчика
    customer_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="ФИО заказчика"
    )

    customer_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Телефон заказчика"
    )

    customer_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Email заказчика"
    )

    # Адрес доставки
    delivery_city: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Город доставки"
    )

    delivery_address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Адрес ПВЗ"
    )

    delivery_city_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Код города СДЭК"
    )

    delivery_point_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Код ПВЗ СДЭК"
    )

    # Стоимость заказа
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Стоимость товаров"
    )

    delivery_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal('0.00'),
        comment="Стоимость доставки"
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal('0.00'),
        comment="Размер скидки"
    )

    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Общая сумма заказа"
    )

    # Промокод
    promocode_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("promocodes.id", ondelete="SET NULL"),
        nullable=True,
        comment="ID использованного промокода"
    )

    promocode_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Код промокода (копия для истории)"
    )

    promocode_discount_percent: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Процент скидки по промокоду"
    )

    # Оплата
    payment_method: Mapped[Optional[PaymentMethod]] = mapped_column(
        Enum(PaymentMethod),
        nullable=True,
        comment="Способ оплаты"
    )

    payment_amount_rub: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Сумма к оплате в рублях"
    )

    payment_amount_usdt: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        comment="Сумма к оплате в USDT"
    )

    payment_wallet: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Кошелек для оплаты"
    )

    payment_unique_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 8),
        nullable=True,
        comment="Уникальная сумма для идентификации платежа"
    )

    # Доставка
    cdek_order_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="ID заказа в системе СДЭК"
    )

    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Трек-номер для отслеживания"
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания заказа"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления"
    )

    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата оплаты"
    )

    shipped_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата отправки"
    )

    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Дата доставки"
    )

    payment_timeout: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Время истечения оплаты"
    )

    # Дополнительная информация
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Заметки к заказу"
    )

    admin_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Заметки администратора"
    )

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="orders",
        lazy="selectin"
    )

    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    promocode: Mapped[Optional["Promocode"]] = relationship(
        "Promocode",
        lazy="selectin"
    )

    payment: Mapped[Optional["Payment"]] = relationship(
        "Payment",
        back_populates="order",
        uselist=False,
        lazy="selectin"
    )

    delivery: Mapped[Optional["Delivery"]] = relationship(
        "Delivery",
        back_populates="order",
        uselist=False,
        lazy="selectin"
    )

    # Индексы
    __table_args__ = (
        Index("idx_order_user_status", "user_id", "status"),
        Index("idx_order_payment_status", "payment_status"),
        Index("idx_order_created", "created_at"),
        Index("idx_order_paid", "paid_at"),
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.id}, number={self.order_number}, status={self.status.value})>"

    @property
    def is_paid(self) -> bool:
        """Проверяет, оплачен ли заказ"""
        return self.payment_status == PaymentStatus.COMPLETED

    @property
    def is_active(self) -> bool:
        """Проверяет, активен ли заказ (не отменен и не возвращен)"""
        return self.status not in [OrderStatus.CANCELLED, OrderStatus.RETURNED]

    @property
    def can_be_paid(self) -> bool:
        """Проверяет, можно ли оплатить заказ"""
        return (
                self.status == OrderStatus.PENDING_PAYMENT
                and self.payment_status in [PaymentStatus.PENDING, PaymentStatus.FAILED]
        )

    @property
    def can_be_cancelled(self) -> bool:
        """Проверяет, можно ли отменить заказ"""
        return self.status in [
            OrderStatus.PENDING_PAYMENT,
            OrderStatus.PAYMENT_PROCESSING,
            OrderStatus.PAID,
            OrderStatus.CONFIRMED
        ]

    @property
    def display_total(self) -> str:
        """Возвращает общую сумму в читаемом формате"""
        return f"{self.total_amount:,.2f} ₽".replace(",", " ")

    @property
    def status_display(self) -> str:
        """Возвращает человекочитаемый статус заказа"""
        status_map = {
            OrderStatus.PENDING_PAYMENT: "Ожидает оплаты",
            OrderStatus.PAYMENT_PROCESSING: "Обработка платежа",
            OrderStatus.PAID: "Оплачен",
            OrderStatus.CONFIRMED: "Подтвержден",
            OrderStatus.ASSEMBLING: "Собирается",
            OrderStatus.SHIPPED: "Отправлен",
            OrderStatus.DELIVERED: "Доставлен",
            OrderStatus.CANCELLED: "Отменен",
            OrderStatus.RETURNED: "Возврат"
        }
        return status_map.get(self.status, self.status.value)

    @property
    def payment_method_display(self) -> str:
        """Возвращает человекочитаемый способ оплаты"""
        if not self.payment_method:
            return "Не выбран"

        method_map = {
            PaymentMethod.USDT_TRC20: "USDT (TRC-20)",
            PaymentMethod.USDT_BEP20: "USDT (BEP-20)",
            PaymentMethod.USDT_TON: "USDT (TON)",
            PaymentMethod.SBP: "СБП"
        }
        return method_map.get(self.payment_method, self.payment_method.value)

    def generate_order_number(self) -> str:
        """Генерирует уникальный номер заказа"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"ORD-{timestamp}-{self.id or 'NEW'}"

    def calculate_totals(self) -> None:
        """Пересчитывает общую сумму заказа"""
        self.subtotal = sum(item.total_price for item in self.items)
        self.total_amount = self.subtotal + self.delivery_cost - self.discount_amount

    def apply_promocode_discount(self, promocode_discount_percent: int) -> None:
        """Применяет скидку по промокоду"""
        discount_decimal = Decimal(promocode_discount_percent) / 100
        self.discount_amount = self.subtotal * discount_decimal
        self.promocode_discount_percent = promocode_discount_percent
        self.calculate_totals()


class OrderItem(Base):
    """Товар в заказе"""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Связи
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        index=True,
        comment="ID заказа"
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        comment="ID товара"
    )

    # Информация о товаре на момент заказа
    product_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Название товара на момент заказа"
    )

    product_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Цена товара на момент заказа"
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Количество товара"
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата добавления в заказ"
    )

    # Связи
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="items"
    )

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="order_items",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product={self.product_name}, qty={self.quantity})>"

    @property
    def total_price(self) -> Decimal:
        """Общая стоимость позиции"""
        return self.product_price * self.quantity

    @property
    def display_price(self) -> str:
        """Цена товара в читаемом формате"""
        return f"{self.product_price:,.2f} ₽".replace(",", " ")

    @property
    def display_total(self) -> str:
        """Общая стоимость в читаемом формате"""
        return f"{self.total_price:,.2f} ₽".replace(",", " ")