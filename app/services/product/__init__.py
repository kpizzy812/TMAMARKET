"""
Сервисы для работы с товарами
Модульная архитектура с разделением ответственности
"""

from .product_crud_service import ProductCRUDService
from .product_catalog_service import ProductCatalogService
from .product_stock_service import ProductStockService
from .product_image_service import ProductImageService

__all__ = [
    "ProductCRUDService",
    "ProductCatalogService",
    "ProductStockService",
    "ProductImageService"
]