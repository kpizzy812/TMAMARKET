"""
Pydantic схемы для товаров
"""

from decimal import Decimal
from typing import Optional, List
from pydantic import field_validator, Field

from app.schemas import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class ProductCreateSchema(BaseCreateSchema):
    """Схема для создания товара"""

    name: str = Field(..., min_length=1, max_length=500, description="Название товара")
    description: Optional[str] = Field(None, max_length=5000, description="Описание товара")
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Цена в рублях")
    image_url: Optional[str] = Field(None, max_length=1000, description="URL изображения")
    detail_url: Optional[str] = Field(None, max_length=1000, description="Ссылка на подробности")

    stock_quantity: int = Field(0, ge=0, description="Количество на складе")
    is_available: bool = Field(True, description="Доступен для заказа")
    is_hidden: bool = Field(False, description="Скрыт из каталога")

    category: Optional[str] = Field(None, max_length=200, description="Категория")
    sort_order: int = Field(0, description="Порядок сортировки")
    tags: Optional[str] = Field(None, description="Теги через запятую")

    # Характеристики
    weight: Optional[Decimal] = Field(None, ge=0, decimal_places=3, description="Вес в граммах")
    dimensions: Optional[str] = Field(None, max_length=100, description="Размеры ДxШxВ см")

    # Лимиты заказа
    min_order_quantity: int = Field(1, ge=1, description="Минимальное количество для заказа")
    max_order_quantity: Optional[int] = Field(None, ge=1, description="Максимальное количество")

    notes: Optional[str] = Field(None, description="Внутренние заметки")

    @field_validator("max_order_quantity")
    @classmethod
    def validate_max_order_quantity(cls, v, info):
        if v is not None and "min_order_quantity" in info.data:
            min_qty = info.data["min_order_quantity"]
            if v < min_qty:
                raise ValueError("Максимальное количество не может быть меньше минимального")
        return v


class ProductUpdateSchema(BaseUpdateSchema):
    """Схема для обновления товара"""

    name: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    image_url: Optional[str] = Field(None, max_length=1000)
    detail_url: Optional[str] = Field(None, max_length=1000)

    stock_quantity: Optional[int] = Field(None, ge=0)
    is_available: Optional[bool] = None
    is_hidden: Optional[bool] = None

    category: Optional[str] = Field(None, max_length=200)
    sort_order: Optional[int] = None
    tags: Optional[str] = None

    weight: Optional[Decimal] = Field(None, ge=0, decimal_places=3)
    dimensions: Optional[str] = Field(None, max_length=100)

    min_order_quantity: Optional[int] = Field(None, ge=1)
    max_order_quantity: Optional[int] = Field(None, ge=1)

    notes: Optional[str] = None


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

    # Вычисляемые поля
    display_price: str
    stock_status: str
    is_in_stock: bool
    is_low_stock: bool
    is_purchasable: bool


class ProductCatalogSchema(BaseSchema):
    """Схема для отображения товара в каталоге"""

    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    display_price: str
    image_url: Optional[str] = None

    is_available: bool
    is_in_stock: bool
    stock_status: str
    is_purchasable: bool

    category: Optional[str] = None
    min_order_quantity: int
    max_order_quantity: Optional[int] = None


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

    @field_validator("max_price")
    @classmethod
    def validate_price_range(cls, v, info):
        if v is not None and "min_price" in info.data and info.data["min_price"] is not None:
            if v <= info.data["min_price"]:
                raise ValueError("Максимальная цена должна быть больше минимальной")
        return v


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
    avg_rating: Optional[float] = None
    last_ordered: Optional[str] = None