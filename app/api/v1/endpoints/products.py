"""
API эндпоинты для работы с товарами
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.api.dependencies.database import get_database_session
from app.api.dependencies.auth import get_current_user_optional, get_admin_user
from app.models.user import User
from app.schemas.product import (
    ProductResponseSchema,
    ProductCatalogSchema,
    ProductAdminSchema,
    ProductCreateSchema,
    ProductUpdateSchema,
    ProductFilterSchema,
    ProductSearchSchema,
    ProductStockUpdateSchema,
    ProductStatsSchema
)
from app.schemas import PaginatedResponseSchema, StatusResponseSchema
from app.services.product_service import ProductService


router = APIRouter()


@router.get(
    "/catalog",
    response_model=PaginatedResponseSchema,
    summary="Получение каталога товаров",
    description="Получение списка товаров для каталога с фильтрацией и пагинацией"
)
async def get_products_catalog(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    search: Optional[str] = Query(None, min_length=2, description="Поиск по названию"),
    min_price: Optional[float] = Query(None, ge=0, description="Минимальная цена"),
    max_price: Optional[float] = Query(None, gt=0, description="Максимальная цена"),
    in_stock: Optional[bool] = Query(None, description="Только товары в наличии"),
    sort_by: str = Query("sort_order", description="Поле для сортировки"),
    sort_desc: bool = Query(False, description="Сортировка по убыванию"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Товаров на странице"),
    session: AsyncSession = Depends(get_database_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Получение каталога товаров для клиентов"""

    try:
        # Создаем фильтры
        filters = ProductFilterSchema(
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            sort_by=sort_by,
            sort_desc=sort_desc,
            page=page,
            per_page=per_page,
            is_available=True,  # Только доступные товары для клиентов
            is_hidden=False     # Только видимые товары
        )

        # Получаем товары через сервис
        product_service = ProductService(session)
        result = await product_service.get_products_catalog(filters, include_hidden=False)

        # Преобразуем в схемы каталога
        catalog_items = [
            ProductCatalogSchema.model_validate(product)
            for product in result["products"]
        ]

        logger.info(f"📦 Каталог запрошен: {len(catalog_items)} товаров, страница {page}")

        return PaginatedResponseSchema(
            items=catalog_items,
            pagination=result["pagination"]
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения каталога: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка загрузки каталога товаров"
        )


@router.get(
    "/{product_id}",
    response_model=ProductResponseSchema,
    summary="Получение товара по ID",
    description="Получение подробной информации о товаре"
)
async def get_product_details(
    product_id: int,
    session: AsyncSession = Depends(get_database_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Получение детальной информации о товаре"""

    try:
        product_service = ProductService(session)
        product = await product_service.get_product_by_id(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )

        # Проверяем доступность для обычных пользователей
        if not current_user or not current_user.is_admin:
            if product.is_hidden or not product.is_available:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Товар недоступен"
                )

        logger.info(f"📦 Запрошен товар: {product.name} (ID: {product_id})")

        return ProductResponseSchema.model_validate(product)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения товара {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка загрузки товара"
        )


@router.post(
    "/search",
    response_model=List[ProductCatalogSchema],
    summary="Поиск товаров",
    description="Поиск товаров по названию, описанию и тегам"
)
async def search_products(
    search_data: ProductSearchSchema,
    session: AsyncSession = Depends(get_database_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Поиск товаров"""

    try:
        product_service = ProductService(session)

        # Дополнительная фильтрация по категории если указана
        if search_data.category:
            filters = ProductFilterSchema(
                search=search_data.query,
                category=search_data.category,
                per_page=search_data.limit,
                is_available=True,
                is_hidden=False
            )
            result = await product_service.get_products_catalog(filters)
            products = result["products"]
        else:
            products = await product_service.search_products(
                search_data.query,
                search_data.limit
            )

        # Преобразуем в схемы каталога
        search_results = [
            ProductCatalogSchema.model_validate(product)
            for product in products
        ]

        logger.info(f"🔍 Поиск '{search_data.query}': найдено {len(search_results)} товаров")

        return search_results

    except Exception as e:
        logger.error(f"❌ Ошибка поиска товаров: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка поиска товаров"
        )


@router.get(
    "/categories/list",
    response_model=List[str],
    summary="Получение списка категорий",
    description="Получение всех доступных категорий товаров"
)
async def get_categories(
    session: AsyncSession = Depends(get_database_session)
):
    """Получение списка всех категорий"""

    try:
        product_service = ProductService(session)
        categories = await product_service.get_categories()

        logger.info(f"📂 Запрошены категории: {len(categories)} найдено")

        return categories

    except Exception as e:
        logger.error(f"❌ Ошибка получения категорий: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка загрузки категорий"
        )


# === АДМИНСКИЕ ЭНДПОИНТЫ ===

@router.get(
    "/admin/all",
    response_model=PaginatedResponseSchema,
    summary="[ADMIN] Получение всех товаров",
    description="Получение всех товаров для админа, включая скрытые",
    dependencies=[Depends(get_admin_user)]
)
async def get_all_products_admin(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    search: Optional[str] = Query(None, description="Поиск по названию"),
    is_available: Optional[bool] = Query(None, description="Фильтр по доступности"),
    is_hidden: Optional[bool] = Query(None, description="Фильтр по видимости"),
    in_stock: Optional[bool] = Query(None, description="Фильтр по наличию"),
    sort_by: str = Query("created_at", description="Поле для сортировки"),
    sort_desc: bool = Query(True, description="Сортировка по убыванию"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(20, ge=1, le=100, description="Товаров на странице"),
    session: AsyncSession = Depends(get_database_session),
    admin_user: User = Depends(get_admin_user)
):
    """Получение всех товаров для администратора"""

    try:
        filters = ProductFilterSchema(
            category=category,
            search=search,
            is_available=is_available,
            is_hidden=is_hidden,
            in_stock=in_stock,
            sort_by=sort_by,
            sort_desc=sort_desc,
            page=page,
            per_page=per_page
        )

        product_service = ProductService(session)
        result = await product_service.get_products_catalog(filters, include_hidden=True)

        # Преобразуем в админские схемы
        admin_items = [
            ProductAdminSchema.model_validate(product)
            for product in result["products"]
        ]

        logger.info(f"⚙️ Админ запросил все товары: {len(admin_items)} найдено")

        return PaginatedResponseSchema(
            items=admin_items,
            pagination=result["pagination"]
        )

    except Exception as e:
        logger.error(f"❌ Ошибка получения товаров для админа: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка загрузки товаров"
        )


@router.post(
    "/admin/create",
    response_model=ProductAdminSchema,
    summary="[ADMIN] Создание товара",
    description="Создание нового товара",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_admin_user)]
)
async def create_product_admin(
    product_data: ProductCreateSchema,
    session: AsyncSession = Depends(get_database_session),
    admin_user: User = Depends(get_admin_user)
):
    """Создание нового товара"""

    try:
        product_service = ProductService(session)
        product = await product_service.create_product(product_data)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка создания товара"
            )

        logger.success(f"⚙️ Админ {admin_user.telegram_id} создал товар: {product.name}")

        return ProductAdminSchema.model_validate(product)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка создания товара: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка создания товара"
        )


@router.put(
    "/admin/{product_id}",
    response_model=ProductAdminSchema,
    summary="[ADMIN] Обновление товара",
    description="Обновление существующего товара",
    dependencies=[Depends(get_admin_user)]
)
async def update_product_admin(
    product_id: int,
    product_data: ProductUpdateSchema,
    session: AsyncSession = Depends(get_database_session),
    admin_user: User = Depends(get_admin_user)
):
    """Обновление товара"""

    try:
        product_service = ProductService(session)
        product = await product_service.update_product(product_id, product_data)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )

        logger.success(f"⚙️ Админ {admin_user.telegram_id} обновил товар: {product.name}")

        return ProductAdminSchema.model_validate(product)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка обновления товара {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления товара"
        )


@router.delete(
    "/admin/{product_id}",
    response_model=StatusResponseSchema,
    summary="[ADMIN] Удаление товара",
    description="Удаление товара из каталога",
    dependencies=[Depends(get_admin_user)]
)
async def delete_product_admin(
    product_id: int,
    session: AsyncSession = Depends(get_database_session),
    admin_user: User = Depends(get_admin_user)
):
    """Удаление товара"""

    try:
        product_service = ProductService(session)
        success = await product_service.delete_product(product_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )

        logger.success(f"⚙️ Админ {admin_user.telegram_id} удалил товар ID: {product_id}")

        return StatusResponseSchema(
            success=True,
            message="Товар успешно удален"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка удаления товара {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка удаления товара"
        )


@router.patch(
    "/admin/{product_id}/stock",
    response_model=StatusResponseSchema,
    summary="[ADMIN] Обновление остатка",
    description="Обновление количества товара на складе",
    dependencies=[Depends(get_admin_user)]
)
async def update_product_stock(
    product_id: int,
    stock_data: ProductStockUpdateSchema,
    session: AsyncSession = Depends(get_database_session),
    admin_user: User = Depends(get_admin_user)
):
    """Обновление остатка товара"""

    try:
        product_service = ProductService(session)
        success = await product_service.update_stock(product_id, stock_data.stock_quantity)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )

        logger.success(f"⚙️ Админ {admin_user.telegram_id} обновил остаток товара {product_id}: {stock_data.stock_quantity}")

        return StatusResponseSchema(
            success=True,
            message=f"Остаток обновлен: {stock_data.stock_quantity} шт."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка обновления остатка товара {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка обновления остатка"
        )


@router.get(
    "/admin/low-stock",
    response_model=List[ProductAdminSchema],
    summary="[ADMIN] Товары с низким остатком",
    description="Получение списка товаров с низким остатком",
    dependencies=[Depends(get_admin_user)]
)
async def get_low_stock_products(
    threshold: Optional[int] = Query(None, ge=1, description="Порог низкого остатка"),
    session: AsyncSession = Depends(get_database_session),
    admin_user: User = Depends(get_admin_user)
):
    """Получение товаров с низким остатком"""

    try:
        product_service = ProductService(session)
        products = await product_service.get_low_stock_products(threshold)

        low_stock_items = [
            ProductAdminSchema.model_validate(product)
            for product in products
        ]

        logger.info(f"⚙️ Админ запросил товары с низким остатком: {len(low_stock_items)} найдено")

        return low_stock_items

    except Exception as e:
        logger.error(f"❌ Ошибка получения товаров с низким остатком: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка загрузки товаров с низким остатком"
        )


@router.post(
    "/admin/{product_id}/image",
    response_model=StatusResponseSchema,
    summary="[ADMIN] Загрузка изображения",
    description="Загрузка изображения для товара",
    dependencies=[Depends(get_admin_user)]
)
async def upload_product_image(
    product_id: int,
    image: UploadFile = File(..., description="Изображение товара"),
    session: AsyncSession = Depends(get_database_session),
    admin_user: User = Depends(get_admin_user)
):
    """Загрузка изображения товара"""

    try:
        # Проверяем тип файла
        if image.content_type not in ["image/jpeg", "image/png", "image/webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Неподдерживаемый тип файла. Разрешены: JPEG, PNG, WebP"
            )

        # Проверяем размер файла
        if image.size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Файл слишком большой. Максимальный размер: 10MB"
            )

        # Читаем данные файла
        image_data = await image.read()

        # Сохраняем через сервис
        product_service = ProductService(session)
        file_path = await product_service.save_product_image(
            product_id, image_data, image.filename
        )

        if not file_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ошибка сохранения изображения"
            )

        logger.success(f"⚙️ Админ {admin_user.telegram_id} загрузил изображение для товара {product_id}")

        return StatusResponseSchema(
            success=True,
            message="Изображение успешно загружено",
            data={"image_path": file_path}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки изображения товара {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка загрузки изображения"
        )


@router.get(
    "/admin/{product_id}/stats",
    response_model=ProductStatsSchema,
    summary="[ADMIN] Статистика товара",
    description="Получение статистики продаж товара",
    dependencies=[Depends(get_admin_user)]
)
async def get_product_stats(
    product_id: int,
    session: AsyncSession = Depends(get_database_session),
    admin_user: User = Depends(get_admin_user)
):
    """Получение статистики товара"""

    try:
        product_service = ProductService(session)
        stats = await product_service.get_product_stats(product_id)

        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Товар не найден"
            )

        logger.info(f"⚙️ Админ запросил статистику товара {product_id}")

        return ProductStatsSchema.model_validate(stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики товара {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка загрузки статистики товара"
        )