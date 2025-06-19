"""
Pydantic схемы для пользователей
"""

from datetime import datetime
from typing import Optional
from pydantic import field_validator, Field

from app.schemas import BaseSchema, BaseCreateSchema, BaseUpdateSchema, BaseResponseSchema


class UserCreateSchema(BaseCreateSchema):
    """Схема для создания пользователя"""

    telegram_id: int = Field(..., description="ID пользователя в Telegram")
    username: Optional[str] = Field(None, max_length=255, description="Username в Telegram")
    first_name: Optional[str] = Field(None, max_length=255, description="Имя")
    last_name: Optional[str] = Field(None, max_length=255, description="Фамилия")
    language_code: Optional[str] = Field(None, max_length=10, description="Код языка")

    @field_validator("telegram_id")
    @classmethod
    def validate_telegram_id(cls, v):
        if v <= 0:
            raise ValueError("Telegram ID должен быть положительным числом")
        return v


class UserUpdateSchema(BaseUpdateSchema):
    """Схема для обновления пользователя"""

    username: Optional[str] = Field(None, max_length=255)
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, max_length=500, description="ФИО для заказов")
    phone: Optional[str] = Field(None, max_length=20, description="Телефон")
    notifications_enabled: Optional[bool] = Field(None, description="Уведомления")
    timezone: Optional[str] = Field(None, max_length=50, description="Часовой пояс")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and not v.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "").isdigit():
            raise ValueError("Некорректный формат телефона")
        return v


class UserResponseSchema(BaseResponseSchema):
    """Схема для ответа с данными пользователя"""

    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool
    is_admin: bool
    is_blocked: bool
    notifications_enabled: bool
    language_code: Optional[str] = None
    timezone: Optional[str] = None
    last_activity: Optional[datetime] = None

    # Вычисляемые поля
    display_name: str
    is_new_user: bool
    total_orders: int

    @field_validator("display_name", mode="before")
    @classmethod
    def get_display_name(cls, v, info):
        """Вычисление отображаемого имени"""
        if hasattr(info.data, "full_name") and info.data.full_name:
            return info.data.full_name

        parts = []
        if hasattr(info.data, "first_name") and info.data.first_name:
            parts.append(info.data.first_name)
        if hasattr(info.data, "last_name") and info.data.last_name:
            parts.append(info.data.last_name)

        if parts:
            return " ".join(parts)

        username = getattr(info.data, "username", None)
        telegram_id = getattr(info.data, "telegram_id", None)

        return username or f"User {telegram_id}"


class UserProfileSchema(BaseSchema):
    """Схема для профиля пользователя (краткая)"""

    id: int
    telegram_id: int
    display_name: str
    username: Optional[str] = None
    is_admin: bool = False
    has_contact_info: bool = False


class UserAdminResponseSchema(UserResponseSchema):
    """Схема для админа с дополнительными полями"""

    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserContactInfoSchema(BaseSchema):
    """Схема для контактной информации"""

    full_name: str = Field(..., min_length=2, max_length=500, description="ФИО")
    phone: str = Field(..., min_length=10, max_length=20, description="Телефон")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        # Простая валидация номера телефона
        clean_phone = v.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        if not clean_phone.isdigit() or len(clean_phone) < 10:
            raise ValueError("Некорректный формат телефона")
        return v


class UserStatsSchema(BaseSchema):
    """Схема для статистики пользователя"""

    total_orders: int = 0
    completed_orders: int = 0
    total_spent: float = 0.0
    promocodes_used: int = 0
    last_order_date: Optional[datetime] = None
    registration_date: datetime