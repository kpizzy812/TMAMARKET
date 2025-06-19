"""
Базовые Pydantic схемы
"""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Базовая схема для всех моделей"""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        arbitrary_types_allowed=True
    )


class BaseCreateSchema(BaseSchema):
    """Базовая схема для создания"""
    pass


class BaseUpdateSchema(BaseSchema):
    """Базовая схема для обновления"""
    pass


class BaseResponseSchema(BaseSchema):
    """Базовая схема для ответов API"""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None


class PaginationSchema(BaseSchema):
    """Схема для пагинации"""

    page: int = 1
    per_page: int = 20
    total: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False


class PaginatedResponseSchema(BaseSchema):
    """Схема для пагинированных ответов"""

    items: list[Any]
    pagination: PaginationSchema


class StatusResponseSchema(BaseSchema):
    """Схема для статусных ответов"""

    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponseSchema(BaseSchema):
    """Схема для ошибок"""

    error: Dict[str, Any]