"""
Модель товара
Хранит информацию о товарах в каталоге
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import (
    String, Text, Boolean, DateTime, Integer,
    Numeric, func, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Product(Base):
    """Модель товара в каталоге"""

    __tablename__ = "products"

    # Основные поля
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Название товара"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Подпись под названием товара"
    )

    # Цена и валюта
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Цена товара в рублях"
    )

    # Изображения и медиа
    image_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="URL основного изображения товара"
    )

    image_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Путь к файлу изображения на сервере"
    )

    detail_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        comment="Ссылка на подробное описание (Telegraph и т.д.)"
    )

    # Остатки и наличие
    stock_quantity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Количество товара на складе"
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Доступен ли товар для заказа"
    )

    is_hidden: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="Скрыт ли товар из каталога"
    )

    # Категоризация и сортировка
    category: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Категория товара"
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Порядок сортировки в каталоге"
    )

    # SEO и теги
    tags: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Теги для поиска (через запятую)"
    )

    # Характеристики товара
    weight: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 3),
        nullable=True,
        comment="Вес товара в граммах"
    )

    dimensions: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Размеры товара (ДxШxВ в см)"
    )

    # Лимиты и ограничения
    min_order_quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="Минимальное количество для заказа"
    )

    max_order_quantity: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Максимальное количество для заказа"
    )

    # Статистика
    views_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Количество просмотров"
    )

    orders_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Количество заказов этого товара"
    )

    # Служебная информация
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Внутренние заметки о товаре"
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания товара"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления"
    )

    # Связи с другими таблицами
    cart_items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="product",
        lazy="selectin"
    )

    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="product",
        lazy="selectin"
    )

    # Индексы для оптимизации запросов
    __table_args__ = (
        Index("idx_product_availability", "is_available", "is_hidden"),
        Index("idx_product_category", "category"),
        Index("idx_product_sort", "sort_order"),
        Index("idx_product_stock", "stock_quantity"),
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', price={self.price})>"

    @property
    def is_in_stock(self) -> bool:
        """Проверяет, есть ли товар в наличии"""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self) -> bool:
        """Проверяет, заканчивается ли товар (< 30 штук)"""
        from app.core.config import marketplace_settings
        return self.stock_quantity < marketplace_settings.LOW_STOCK_THRESHOLD

    @property
    def is_purchasable(self) -> bool:
        """Проверяет, можно ли купить товар"""
        return (
                self.is_available
                and not self.is_hidden
                and self.is_in_stock
        )

    @property
    def display_price(self) -> str:
        """Возвращает цену в читаемом формате"""
        return f"{self.price:,.2f} ₽".replace(",", " ")

    @property
    def stock_status(self) -> str:
        """Возвращает статус наличия товара"""
        if not self.is_available:
            return "Недоступен"
        if not self.is_in_stock:
            return "Нет в наличии"
        if self.is_low_stock:
            return f"Заканчивается ({self.stock_quantity} шт.)"
        return f"В наличии ({self.stock_quantity} шт.)"

    def can_order_quantity(self, quantity: int) -> bool:
        """
        Проверяет, можно ли заказать указанное количество

        Args:
            quantity: Желаемое количество

        Returns:
            bool: Можно ли заказать
        """
        if not self.is_purchasable:
            return False

        if quantity < self.min_order_quantity:
            return False

        if self.max_order_quantity and quantity > self.max_order_quantity:
            return False

        return quantity <= self.stock_quantity

    def get_max_available_quantity(self) -> int:
        """
        Возвращает максимальное доступное количество для заказа

        Returns:
            int: Максимальное количество
        """
        if not self.is_purchasable:
            return 0

        max_qty = self.stock_quantity

        if self.max_order_quantity:
            max_qty = min(max_qty, self.max_order_quantity)

        return max(0, max_qty)

    async def update_stock(self, quantity_change: int) -> bool:
        """
        Обновляет количество товара на складе

        Args:
            quantity_change: Изменение количества (может быть отрицательным)

        Returns:
            bool: Успешно ли обновлено
        """
        new_quantity = self.stock_quantity + quantity_change

        if new_quantity < 0:
            return False

        self.stock_quantity = new_quantity
        return True

    def increment_views(self) -> None:
        """Увеличивает счетчик просмотров"""
        self.views_count += 1

    def increment_orders(self) -> None:
        """Увеличивает счетчик заказов"""
        self.orders_count += 1