"""
Pydantic схемы для товаров
"""

from decimal import Decimal
from typing import Optional, List, Annotated
from pydantic import field_validator, Field, computed_field, model_validator

from app.schemas import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class ProductCreateSchema(BaseCreateSchema):
    """Схема для создания товара"""

    name: str = Field(..., min_length=1, max_length=500, description="Название товара")
    description: Optional[str] = Field(None, max_length=5000, description="Описание товара")
    price: Decimal = Field(..., gt=0, description="Цена в рублях")
    image_url: Optional[str] = Field(None, max_length=1000, description="URL изображения")
    detail_url: Optional[str] = Field(None, max_length=1000, description="Ссылка на подробности")

    stock_quantity: int = Field(0, ge=0, description="Количество на складе")
    is_available: bool = Field(True, description="Доступен для заказа")
    is_hidden: bool = Field(False, description="Скрыт из каталога")

    category: Optional[str] = Field(None, max_length=200, description="Категория")
    sort_order: int = Field(0, description="Порядок сортировки")
    tags: Optional[str] = Field(None, description="Теги через запятую")

    # Характеристики
    weight: Optional[Decimal] = Field(None, ge=0, description="Вес в граммах")
    dimensions: Optional[str] = Field(None, max_length=100, description="Размеры ДxШxВ см")

    # Лимиты заказа
    min_order_quantity: int = Field(1, ge=1, description="Минимальное количество для заказа")
    max_order_quantity: Optional[int] = Field(None, ge=1, description="Максимальное количество")

    notes: Optional[str] = Field(None, description="Внутренние заметки")

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Цена должна быть больше 0")
        # Ограничиваем до 2 знаков после запятой
        return v.quantize(Decimal('0.01'))

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError("Вес не может быть отрицательным")
            # Ограничиваем до 3 знаков после запятой
            return v.quantize(Decimal('0.001'))
        return v

    @model_validator(mode='after')
    def validate_order_quantities(self):
        if self.max_order_quantity is not None and self.max_order_quantity < self.min_order_quantity:
            raise ValueError("Максимальное количество не может быть меньше минимального")
        return self


class ProductUpdateSchema(BaseUpdateSchema):
    """Схема для обновления товара"""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    price: Optional[Decimal] = Field(None, gt=0, description="Цена в рублях")
    image_url: Optional[str] = Field(None, max_length=1000)
    detail_url: Optional[str] = Field(None, max_length=1000)

    stock_quantity: Optional[int] = Field(None, ge=0)
    is_available: Optional[bool] = None
    is_hidden: Optional[bool] = None

    category: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None
    tags: Optional[str] = None

    weight: Optional[Decimal] = Field(None, ge=0, description="Вес в граммах")
    dimensions: Optional[str] = Field(None, max_length=100)

    min_order_quantity: Optional[int] = Field(None, ge=1)
    max_order_quantity: Optional[int] = Field(None, ge=1)

    notes: Optional[str] = None

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        if v is not None:
            if v <= 0:
                raise ValueError("Цена должна быть больше 0")
            return v.quantize(Decimal('0.01'))
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v):
        if v is not None:
            if v < 0:
                raise ValueError("Вес не может быть отрицательным")
            return v.quantize(Decimal('0.001'))
        return v


class ProductResponseSchema(BaseResponseSchema):
    """Схема для ответа с данными товара"""

    name: str
    description: Optional[str] = None
    price: Decimal
    image_url: Optional[str] = None
    detail_url: Optional[str] = None

    stock_quantity: int
    is_available: bool
    is_hidden: bool

    category: Optional[str] = None
    sort_order: int
    tags: Optional[str] = None

    weight: Optional[Decimal] = None
    dimensions: Optional[str] = None

    min_order_quantity: int
    max_order_quantity: Optional[int] = None

    views_count: int
    orders_count: int

    @computed_field
    @property
    def display_price(self) -> str:
        """Цена в читаемом формате"""
        return f"{self.price:,.2f} ₽".replace(",", " ")

    @computed_field
    @property
    def stock_status(self) -> str:
        """Статус наличия товара"""
        if not self.is_available:
            return "Недоступен"
        if self.stock_quantity <= 0:
            return "Нет в наличии"
        if self.stock_quantity < 30:  # LOW_STOCK_THRESHOLD
            return f"Заканчивается ({self.stock_quantity} шт.)"
        return f"В наличии ({self.stock_quantity} шт.)"

    @computed_field
    @property
    def is_in_stock(self) -> bool:
        """Есть ли товар в наличии"""
        return self.stock_quantity > 0

    @computed_field
    @property
    def is_low_stock(self) -> bool:
        """Заканчивается ли товар"""
        return self.stock_quantity < 30  # LOW_STOCK_THRESHOLD

    @computed_field
    @property
    def is_purchasable(self) -> bool:
        """Можно ли купить товар"""
        return self.is_available and not self.is_hidden and self.is_in_stock


class ProductCatalogSchema(BaseSchema):
    """Схема для отображения товара в каталоге"""

    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    image_url: Optional[str] = None

    is_available: bool
    stock_quantity: int

    category: Optional[str] = None
    min_order_quantity: int
    max_order_quantity: Optional[int] = None

    @computed_field
    @property
    def display_price(self) -> str:
        """Цена в читаемом формате"""
        return f"{self.price:,.2f} ₽".replace(",", " ")

    @computed_field
    @property
    def is_in_stock(self) -> bool:
        """Есть ли товар в наличии"""
        return self.stock_quantity > 0

    @computed_field
    @property
    def stock_status(self) -> str:
        """Статус наличия товара"""
        if not self.is_available:
            return "Недоступен"
        if self.stock_quantity <= 0:
            return "Нет в наличии"
        if self.stock_quantity < 30:
            return f"Заканчивается ({self.stock_quantity} шт.)"
        return f"В наличии ({self.stock_quantity} шт.)"

    @computed_field
    @property
    def is_purchasable(self) -> bool:
        """Можно ли купить товар"""
        return self.is_available and self.is_in_stock


class ProductAdminSchema(ProductResponseSchema):
    """Схема для админа с дополнительными полями"""

    notes: Optional[str] = None


class ProductStockUpdateSchema(BaseSchema):
    """Схема для обновления остатков"""

    stock_quantity: int = Field(..., ge=0, description="Новое количество на складе")


class ProductFilterSchema(BaseSchema):
    """Схема для фильтрации товаров"""

    category: Optional[str] = None
    is_available: Optional[bool] = None
    is_hidden: Optional[bool] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, gt=0)
    in_stock: Optional[bool] = None
    search: Optional[str] = Field(None, min_length=2, description="Поиск по названию")

    # Сортировка
    sort_by: Optional[str] = Field("sort_order", description="Поле сортировки")
    sort_desc: bool = Field(False, description="По убыванию")

    # Пагинация
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

    @model_validator(mode='after')
    def validate_price_range(self):
        if self.max_price is not None and self.min_price is not None:
            if self.max_price <= self.min_price:
                raise ValueError("Максимальная цена должна быть больше минимальной")
        return self


class ProductSearchSchema(BaseSchema):
    """Схема для поиска товаров"""

    query: str = Field(..., min_length=2, max_length=100, description="Поисковый запрос")
    category: Optional[str] = None
    limit: int = Field(10, ge=1, le=50, description="Количество результатов")


class ProductStatsSchema(BaseSchema):
    """Схема для статистики товара"""

    views_count: int
    orders_count: int
    total_ordered_quantity: int
    revenue: Decimal
    current_stock: int
    is_low_stock: bool