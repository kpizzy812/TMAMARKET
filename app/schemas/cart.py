"""
Pydantic схемы для корзины
"""

from decimal import Decimal
from typing import List, Optional
from pydantic import Field, field_validator

from app.schemas import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema
from app.schemas.product import ProductCatalogSchema


class CartItemCreateSchema(BaseCreateSchema):
    """Схема для добавления товара в корзину"""

    product_id: int = Field(..., gt=0, description="ID товара")
    quantity: int = Field(1, ge=1, le=99, description="Количество")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError("Количество должно быть больше 0")
        if v > 99:
            raise ValueError("Максимальное количество: 99")
        return v


class CartItemUpdateSchema(BaseUpdateSchema):
    """Схема для обновления товара в корзине"""

    quantity: int = Field(..., ge=1, le=99, description="Новое количество")

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError("Количество должно быть больше 0")
        if v > 99:
            raise ValueError("Максимальное количество: 99")
        return v


class CartItemResponseSchema(BaseResponseSchema):
    """Схема для элемента корзины"""

    product_id: int
    quantity: int
    price_at_add: Decimal

    # Связанный товар
    product: ProductCatalogSchema

    # Вычисляемые поля
    total_price: Decimal
    current_total_price: Decimal
    price_changed: bool
    is_available: bool
    max_available_quantity: int


class CartResponseSchema(BaseSchema):
    """Схема для корзины"""

    items: List[CartItemResponseSchema] = []

    # Итоговые суммы
    total_items: int
    total_quantity: int
    subtotal: Decimal
    delivery_cost: Decimal
    total: Decimal

    # Информация о доставке
    free_delivery_threshold: Decimal
    is_free_delivery: bool

    # Валидация корзины
    is_valid: bool
    issues: List[dict] = []


class CartSummarySchema(BaseSchema):
    """Схема для краткой информации о корзине"""

    total_items: int
    total_quantity: int
    total: Decimal
    is_valid: bool


class CartValidationSchema(BaseSchema):
    """Схема для результата валидации корзины"""

    is_valid: bool
    issues: List[dict] = []
    valid_items: List[CartItemResponseSchema] = []
    total_issues: int


class CartTotalsSchema(BaseSchema):
    """Схема для подсчета итогов корзины"""

    subtotal: Decimal = Field(..., description="Стоимость товаров")
    delivery_cost: Decimal = Field(..., description="Стоимость доставки")
    discount_amount: Decimal = Field(Decimal('0.00'), description="Размер скидки")
    total: Decimal = Field(..., description="Итоговая сумма")

    free_delivery_threshold: Decimal
    is_free_delivery: bool

    # Детали
    total_items: int
    total_quantity: int


class PromocodeApplicationSchema(BaseSchema):
    """Схема для применения промокода к корзине"""

    promocode: str = Field(..., min_length=3, max_length=50, description="Код промокода")


class PromocodeApplicationResultSchema(BaseSchema):
    """Схема для результата применения промокода"""

    success: bool
    message: str
    promocode_code: Optional[str] = None
    discount_percent: Optional[int] = None
    discount_amount: Optional[Decimal] = None

    # Новые итоги после применения
    new_totals: Optional[CartTotalsSchema] = None


class CartCheckoutSchema(BaseSchema):
    """Схема для данных при оформлении заказа"""

    # Контактная информация
    customer_name: str = Field(..., min_length=2, max_length=500, description="ФИО")
    customer_phone: str = Field(..., min_length=10, max_length=20, description="Телефон")
    customer_email: Optional[str] = Field(None, max_length=255, description="Email")

    # Доставка
    delivery_city: str = Field(..., min_length=2, max_length=200, description="Город")
    delivery_address: str = Field(..., min_length=5, description="Адрес ПВЗ")
    delivery_city_code: Optional[str] = Field(None, max_length=20, description="Код города СДЭК")
    delivery_point_code: Optional[str] = Field(None, max_length=20, description="Код ПВЗ")

    # Промокод
    promocode: Optional[str] = Field(None, min_length=3, max_length=50, description="Промокод")

    # Заметки
    notes: Optional[str] = Field(None, max_length=1000, description="Комментарий к заказу")

    @field_validator("customer_phone")
    @classmethod
    def validate_phone(cls, v):
        # Простая валидация телефона
        clean_phone = v.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        if not clean_phone.isdigit() or len(clean_phone) < 10:
            raise ValueError("Некорректный формат телефона")
        return v

    @field_validator("customer_email")
    @classmethod
    def validate_email(cls, v):
        if v:
            import re
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, v):
                raise ValueError("Некорректный формат email")
        return v


class CartClearSchema(BaseSchema):
    """Схема для очистки корзины"""

    confirm: bool = Field(..., description="Подтверждение очистки")

    @field_validator("confirm")
    @classmethod
    def validate_confirm(cls, v):
        if not v:
            raise ValueError("Требуется подтверждение очистки корзины")
        return v


class CartBulkUpdateSchema(BaseSchema):
    """Схема для массового обновления корзины"""

    items: List[dict] = Field(..., min_length=1, description="Список обновлений")

    @field_validator("items")
    @classmethod
    def validate_items(cls, v):
        for item in v:
            if "product_id" not in item or "quantity" not in item:
                raise ValueError("Каждый элемент должен содержать product_id и quantity")
            if not isinstance(item["product_id"], int) or item["product_id"] <= 0:
                raise ValueError("product_id должен быть положительным числом")
            if not isinstance(item["quantity"], int) or item["quantity"] < 1:
                raise ValueError("quantity должен быть больше 0")
        return v