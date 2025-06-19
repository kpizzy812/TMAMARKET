"""
Модели корзины покупок
Хранит товары, добавленные пользователем в корзину
"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlalchemy import (
    String, Boolean, DateTime, Integer,
    Numeric, ForeignKey, func, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Cart(Base):
    """
    Корзина пользователя (опционально, для сохранения состояния)
    В основном используется CartItem напрямую
    """

    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Связь с пользователем
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="ID пользователя"
    )

    # Временные метки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата создания корзины"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления"
    )

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="cart_items"
    )

    items: Mapped[List["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Cart(id={self.id}, user_id={self.user_id}, items_count={len(self.items)})>"


class CartItem(Base):
    """Товар в корзине пользователя"""

    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Связи
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        comment="ID пользователя"
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
        comment="ID товара"
    )

    cart_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=True,
        comment="ID корзины (опционально)"
    )

    # Количество и цена
    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
        comment="Количество товара в корзине"
    )

    # Цена на момент добавления (для отслеживания изменений)
    price_at_add: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Цена товара на момент добавления в корзину"
    )

    # Временные метки
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата добавления в корзину"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата последнего обновления"
    )

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="cart_items"
    )

    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="cart_items",
        lazy="selectin"
    )

    cart: Mapped[Optional["Cart"]] = relationship(
        "Cart",
        back_populates="items"
    )

    # Ограничения и индексы
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uq_user_product_cart"),
        Index("idx_cart_item_user", "user_id"),
        Index("idx_cart_item_product", "product_id"),
        Index("idx_cart_item_updated", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<CartItem(id={self.id}, user_id={self.user_id}, product_id={self.product_id}, quantity={self.quantity})>"

    @property
    def total_price(self) -> Decimal:
        """Общая стоимость позиции в корзине"""
        return self.price_at_add * self.quantity

    @property
    def current_product_price(self) -> Decimal:
        """Текущая цена товара"""
        return self.product.price if self.product else self.price_at_add

    @property
    def current_total_price(self) -> Decimal:
        """Общая стоимость по текущей цене товара"""
        return self.current_product_price * self.quantity

    @property
    def price_changed(self) -> bool:
        """Проверяет, изменилась ли цена товара с момента добавления"""
        return self.price_at_add != self.current_product_price

    @property
    def is_available(self) -> bool:
        """Проверяет, доступен ли товар для заказа"""
        if not self.product:
            return False
        return self.product.is_purchasable

    @property
    def max_available_quantity(self) -> int:
        """Максимальное доступное количество товара"""
        if not self.product:
            return 0
        return self.product.get_max_available_quantity()

    def can_increase_quantity(self, amount: int = 1) -> bool:
        """
        Проверяет, можно ли увеличить количество

        Args:
            amount: На сколько увеличить

        Returns:
            bool: Можно ли увеличить
        """
        if not self.product:
            return False

        new_quantity = self.quantity + amount
        return self.product.can_order_quantity(new_quantity)

    def can_decrease_quantity(self, amount: int = 1) -> bool:
        """
        Проверяет, можно ли уменьшить количество

        Args:
            amount: На сколько уменьшить

        Returns:
            bool: Можно ли уменьшить
        """
        new_quantity = self.quantity - amount
        return new_quantity >= 1

    def update_quantity(self, new_quantity: int) -> bool:
        """
        Обновляет количество товара в корзине

        Args:
            new_quantity: Новое количество

        Returns:
            bool: Успешно ли обновлено
        """
        if new_quantity < 1:
            return False

        if not self.product:
            return False

        if not self.product.can_order_quantity(new_quantity):
            return False

        self.quantity = new_quantity
        return True

    def sync_price(self) -> None:
        """Синхронизирует цену с текущей ценой товара"""
        if self.product:
            self.price_at_add = self.product.price


# Вспомогательные функции для работы с корзиной
class CartHelper:
    """Вспомогательный класс для операций с корзиной"""

    @staticmethod
    def calculate_cart_total(cart_items: List[CartItem]) -> dict:
        """
        Рассчитывает общую стоимость корзины

        Args:
            cart_items: Список товаров в корзине

        Returns:
            dict: Информация о стоимости корзины
        """
        from app.core.config import marketplace_settings

        total_items = len(cart_items)
        total_quantity = sum(item.quantity for item in cart_items)

        # Стоимость товаров
        subtotal = sum(item.current_total_price for item in cart_items)

        # Стоимость доставки
        delivery_cost = Decimal(marketplace_settings.DELIVERY_COST)
        free_delivery_threshold = Decimal(marketplace_settings.FREE_DELIVERY_THRESHOLD)

        if subtotal >= free_delivery_threshold:
            delivery_cost = Decimal('0.00')

        # Общая стоимость
        total = subtotal + delivery_cost

        return {
            'total_items': total_items,
            'total_quantity': total_quantity,
            'subtotal': subtotal,
            'delivery_cost': delivery_cost,
            'total': total,
            'free_delivery_threshold': free_delivery_threshold,
            'is_free_delivery': delivery_cost == 0
        }

    @staticmethod
    def validate_cart_items(cart_items: List[CartItem]) -> dict:
        """
        Проверяет корзину на доступность товаров

        Args:
            cart_items: Список товаров в корзине

        Returns:
            dict: Результат валидации
        """
        issues = []
        valid_items = []

        for item in cart_items:
            if not item.is_available:
                issues.append({
                    'item': item,
                    'issue': 'unavailable',
                    'message': 'Товар недоступен'
                })
                continue

            if not item.product.can_order_quantity(item.quantity):
                max_qty = item.max_available_quantity
                issues.append({
                    'item': item,
                    'issue': 'quantity',
                    'message': f'Доступно только {max_qty} шт.',
                    'max_quantity': max_qty
                })
                continue

            if item.price_changed:
                issues.append({
                    'item': item,
                    'issue': 'price_changed',
                    'message': 'Цена товара изменилась',
                    'old_price': item.price_at_add,
                    'new_price': item.current_product_price
                })

            valid_items.append(item)

        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'valid_items': valid_items,
            'total_issues': len(issues)
        }