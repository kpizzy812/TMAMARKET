"""
CORS Middleware
Настройка кросс-доменных запросов
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings


def setup_cors(app: FastAPI) -> None:
    """
    Настройка CORS для FastAPI приложения

    Args:
        app: Экземпляр FastAPI
    """

    # Разрешенные origins
    allowed_origins = []

    # В режиме разработки разрешаем все
    if settings.DEBUG:
        allowed_origins = ["*"]
        logger.warning("🔓 CORS: Разрешены все origins (режим разработки)")
    else:
        # В продакшене используем настройки из конфига
        allowed_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
        logger.info(f"🔒 CORS: Разрешенные origins: {allowed_origins}")

    # Добавляем middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS"
        ],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "X-API-Key",
            "X-User-ID",
            "Accept",
            "Origin",
            "Cache-Control"
        ],
        expose_headers=[
            "X-Total-Count",
            "X-Page-Count",
            "X-Rate-Limit-Remaining",
            "X-Request-ID"
        ]
    )

    logger.success("✅ CORS middleware настроен")