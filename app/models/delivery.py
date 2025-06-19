"""
Модель доставки
Интеграция с СДЭК и отслеживание доставок
"""

import enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    String, Text, Boolean, DateTime, Integer,
    Numeric, ForeignKey, func, Index, Enum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class DeliveryStatus(enum.Enum):
    """Статусы доставки"""
    CREATED = "created"  # Создана
    REGISTERED = "registered"  # Зарегистрирована в СДЭК
    ACCEPTED = "accepted"  # Принята к доставке
    READY_FOR_SHIPMENT = "ready_for_shipment"  # Готова к отправке
    SENT_FROM_SENDER_CITY = "sent_from_sender_city"  # Отправлена из города отправителя
    ARRIVED_AT_TRANSIT = "arrived_at_transit"  # Прибыла в транзитный пункт
    SENT_FROM_TRANSIT = "sent_from_transit"  # Отправлена из транзитного пункта
    ARRIVED_AT_DESTINATION = "arrived_at_destination"  # Прибыла в город назначения
    READY_FOR_PICKUP = "ready_for_pickup"  # Готова к выдаче
    DELIVERED = "delivered"  # Доставлена
    NOT_DELIVERED = "not_delivered"  # Не доставлена
    RETURNED = "returned"  # Возвращена отправителю
    CANCELLED = "cancelled"  # Отменена


class DeliveryProvider(enum.Enum):
    """Службы доставки"""
    CDEK = "cdek"
    MANUAL = "manual"  # Ручная доставка


class Delivery(Base):
    """Модель доставки"""

    __tablename__ = "deliveries"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Связь с заказом
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        comment="ID заказа"
    )

    # Провайдер доставки
    provider: Mapped[DeliveryProvider] = mapped_column(
        Enum(DeliveryProvider),
        default=DeliveryProvider.CDEK,
        comment="Служба доставки"
    )

    # Статус доставки
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus),
        default=DeliveryStatus.CREATED,
        index=True,
        comment="Статус доставки"
    )

    # СДЭК данные
    cdek_order_uuid: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="UUID заказа в системе СДЭК"
    )

    cdek_order_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Номер заказа в СДЭК"
    )

    tracking_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Трек-номер для отслеживания"
    )

    # Информация о доставке
    sender_city_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Код города отправителя"
    )

    recipient_city_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Код города получателя"
    )

    recipient_city_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Название города получателя"
    )

    pickup_point_code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Код пункта выдачи"
    )

    pickup_point_address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Адрес пункта выдачи"
    )

    # Получатель
    recipient_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="ФИО получателя"
    )

    recipient_phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Телефон получателя"
    )

    recipient_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Email получателя"
    )

    # Параметры доставки
    tariff_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Код тарифа СДЭК"
    )

    delivery_cost: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal('500.00'),
        comment="Стоимость доставки"
    )

    declared_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Объявленная стоимость"
    )

    # Временные рамки
    estimated_delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ожидаемая дата доставки"
    )

    delivery_period_min: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Минимальный срок доставки (дни)"
    )

    delivery_period_max: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Максимальный срок доставки (дни)"
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
        comment="Дата обновления"
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

    last_status_check: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Последняя проверка статуса"
    )

    # Дополнительные данные
    cdek_response_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Ответ от API СДЭК (JSON)"
    )

    tracking_events: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
        comment="События отслеживания (JSON)"
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Заметки к доставке"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Сообщение об ошибке"
    )

    # Связи
    order: Mapped["Order"] = relationship(
        "Order",
        back_populates="delivery",
        lazy="selectin"
    )

    # Индексы
    __table_args__ = (
        Index("idx_delivery_status_provider", "status", "provider"),
        Index("idx_delivery_tracking", "tracking_number"),
        Index("idx_delivery_cdek_uuid", "cdek_order_uuid"),
        Index("idx_delivery_city", "recipient_city_code"),
    )

    def __repr__(self) -> str:
        return f"<Delivery(id={self.id}, order_id={self.order_id}, status={self.status.value})>"

    @property
    def is_delivered(self) -> bool:
        """Проверяет, доставлен ли заказ"""
        return self.status == DeliveryStatus.DELIVERED

    @property
    def is_in_transit(self) -> bool:
        """Проверяет, в пути ли заказ"""
        transit_statuses = [
            DeliveryStatus.SENT_FROM_SENDER_CITY,
            DeliveryStatus.ARRIVED_AT_TRANSIT,
            DeliveryStatus.SENT_FROM_TRANSIT,
            DeliveryStatus.ARRIVED_AT_DESTINATION
        ]
        return self.status in transit_statuses

    @property
    def is_ready_for_pickup(self) -> bool:
        """Проверяет, готов ли заказ к выдаче"""
        return self.status == DeliveryStatus.READY_FOR_PICKUP

    @property
    def has_tracking_number(self) -> bool:
        """Проверяет, есть ли трек-номер"""
        return bool(self.tracking_number)

    @property
    def tracking_url(self) -> Optional[str]:
        """Возвращает ссылку для отслеживания"""
        if not self.tracking_number:
            return None

        if self.provider == DeliveryProvider.CDEK:
            return f"https://www.cdek.ru/ru/tracking/?order_id={self.tracking_number}"

        return None

    @property
    def status_display(self) -> str:
        """Возвращает человекочитаемый статус доставки"""
        status_map = {
            DeliveryStatus.CREATED: "Создана",
            DeliveryStatus.REGISTERED: "Зарегистрирована",
            DeliveryStatus.ACCEPTED: "Принята к доставке",
            DeliveryStatus.READY_FOR_SHIPMENT: "Готова к отправке",
            DeliveryStatus.SENT_FROM_SENDER_CITY: "Отправлена",
            DeliveryStatus.ARRIVED_AT_TRANSIT: "В пути",
            DeliveryStatus.SENT_FROM_TRANSIT: "В пути",
            DeliveryStatus.ARRIVED_AT_DESTINATION: "Прибыла в город",
            DeliveryStatus.READY_FOR_PICKUP: "Готова к выдаче",
            DeliveryStatus.DELIVERED: "Доставлена",
            DeliveryStatus.NOT_DELIVERED: "Не доставлена",
            DeliveryStatus.RETURNED: "Возвращена",
            DeliveryStatus.CANCELLED: "Отменена"
        }
        return status_map.get(self.status, self.status.value)

    @property
    def delivery_days_estimate(self) -> Optional[str]:
        """Возвращает оценку времени доставки"""
        if self.delivery_period_min and self.delivery_period_max:
            if self.delivery_period_min == self.delivery_period_max:
                return f"{self.delivery_period_min} дн."
            return f"{self.delivery_period_min}-{self.delivery_period_max} дн."
        return None

    def update_status(self, new_status: DeliveryStatus, event_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Обновляет статус доставки

        Args:
            new_status: Новый статус
            event_data: Дополнительные данные о событии
        """
        old_status = self.status
        self.status = new_status

        # Обновляем временные метки
        if new_status in [DeliveryStatus.SENT_FROM_SENDER_CITY, DeliveryStatus.READY_FOR_SHIPMENT]:
            self.shipped_at = datetime.now()
        elif new_status == DeliveryStatus.DELIVERED:
            self.delivered_at = datetime.now()

        # Добавляем событие в историю
        if event_data:
            self.add_tracking_event(
                status=new_status.value,
                description=f"Статус изменен с {old_status.value} на {new_status.value}",
                event_data=event_data
            )

    def add_tracking_event(self, status: str, description: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Добавляет событие отслеживания

        Args:
            status: Статус события
            description: Описание события
            event_data: Дополнительные данные
        """
        if self.tracking_events is None:
            self.tracking_events = []

        event = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "description": description,
            "data": event_data or {}
        }

        self.tracking_events.append(event)

    def get_latest_tracking_event(self) -> Optional[Dict[str, Any]]:
        """Возвращает последнее событие отслеживания"""
        if not self.tracking_events:
            return None
        return self.tracking_events[-1]

    def should_check_status(self) -> bool:
        """Проверяет, нужно ли обновлять статус доставки"""
        # Не проверяем финальные статусы
        if self.status in [DeliveryStatus.DELIVERED, DeliveryStatus.CANCELLED, DeliveryStatus.RETURNED]:
            return False

        # Проверяем только если есть трек-номер
        if not self.tracking_number:
            return False

        # Не проверяем слишком часто (раз в час)
        if self.last_status_check:
            time_since_check = datetime.now() - self.last_status_check
            if time_since_check.total_seconds() < 3600:  # 1 час
                return False

        return True

    def mark_status_checked(self) -> None:
        """Отмечает время последней проверки статуса"""
        self.last_status_check = datetime.now()

    def calculate_delivery_cost(self, order_total: Decimal, free_threshold: Decimal = Decimal('2000')) -> Decimal:
        """
        Рассчитывает стоимость доставки

        Args:
            order_total: Общая сумма заказа
            free_threshold: Порог бесплатной доставки

        Returns:
            Decimal: Стоимость доставки
        """
        if order_total >= free_threshold:
            return Decimal('0.00')
        return self.delivery_cost

    def generate_tracking_message(self) -> str:
        """Генерирует сообщение для клиента с информацией о доставке"""
        message_parts = [
            f"📦 Статус доставки: {self.status_display}"
        ]

        if self.tracking_number:
            message_parts.append(f"🔍 Трек-номер: {self.tracking_number}")

        if self.tracking_url:
            message_parts.append(f"🔗 Отследить: {self.tracking_url}")

        if self.estimated_delivery_date:
            date_str = self.estimated_delivery_date.strftime("%d.%m.%Y")
            message_parts.append(f"📅 Ожидаемая доставка: {date_str}")
        elif self.delivery_days_estimate:
            message_parts.append(f"⏱ Срок доставки: {self.delivery_days_estimate}")

        return "\n".join(message_parts)