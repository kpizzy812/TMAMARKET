"""
Основное FastAPI приложение
Telegram Marketplace Backend
"""

import sys
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings, telegram_settings
from app.core.database import create_tables
from app.middleware.cors import setup_cors
from app.middleware.error_handler import setup_error_handlers
from app.api.v1.api import api_router


def setup_logging() -> None:
    """Настройка логирования через loguru"""

    # Удаляем стандартный обработчик
    logger.remove()

    # Консольное логирование с красивым форматом
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level="DEBUG" if settings.DEBUG else "INFO",
        colorize=True,
        backtrace=True,
        diagnose=True
    )

    # Файловое логирование
    logger.add(
        "logs/app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=False  # Безопасность в продакшене
    )

    # Отдельный файл для ошибок
    logger.add(
        "logs/error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="5 MB",
        retention="90 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )

    # Логи API запросов
    logger.add(
        "logs/api.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {extra[method]} {extra[url]} | "
               "Status: {extra[status_code]} | Duration: {extra[duration]}ms | {message}",
        level="INFO",
        rotation="20 MB",
        retention="14 days",
        filter=lambda record: "api_request" in record["extra"]
    )

    logger.info("Логирование настроено")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""

    # Startup
    logger.info("🚀 Запуск Telegram Marketplace...")

    try:
        # Создание таблиц БД
        logger.info("📊 Создание таблиц базы данных...")
        await create_tables()
        logger.success("✅ База данных готова")

        # Инициализация других сервисов
        logger.info("🔧 Инициализация сервисов...")

        # TODO: Инициализация Telegram бота
        # TODO: Инициализация планировщика задач
        # TODO: Инициализация Redis

        logger.success("✅ Все сервисы запущены")
        logger.info(f"🌟 {settings.PROJECT_NAME} v{settings.VERSION} готов к работе!")

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Остановка приложения...")

    try:
        # Корректное закрытие соединений
        # TODO: Остановка Telegram бота
        # TODO: Закрытие Redis соединений
        # TODO: Остановка планировщика

        logger.success("✅ Приложение корректно остановлено")

    except Exception as e:
        logger.error(f"❌ Ошибка при остановке: {e}")


def create_application() -> FastAPI:
    """Создание и настройка FastAPI приложения"""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="Backend API для Telegram маркетплейса с поддержкой USDT и СБП платежей",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan
    )

    # Настройка CORS
    setup_cors(app)

    # Настройка обработки ошибок
    setup_error_handlers(app)

    # Middleware для логирования запросов
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        # Логируем входящий запрос
        logger.bind(
            method=request.method,
            url=str(request.url),
            api_request=True
        ).info(f"📨 {request.method} {request.url.path}")

        try:
            response = await call_next(request)

            # Вычисляем время обработки
            duration = round((time.time() - start_time) * 1000, 2)

            # Логируем ответ
            level = "error" if response.status_code >= 400 else "info"
            logger.bind(
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                duration=duration,
                api_request=True
            ).log(level, f"📤 Response {response.status_code}")

            return response

        except Exception as e:
            duration = round((time.time() - start_time) * 1000, 2)
            logger.bind(
                method=request.method,
                url=str(request.url),
                status_code=500,
                duration=duration,
                api_request=True
            ).error(f"💥 Ошибка: {e}")
            raise

    # Подключение роутеров
    app.include_router(
        api_router,
        prefix=settings.API_V1_STR
    )

    return app


# Настройка логирования
setup_logging()

# Создание приложения
app = create_application()


@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


@app.get("/", tags=["Root"])
async def root():
    """Корневой эндпоинт"""
    return {
        "message": f"🛍️ {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else "Disabled in production"
    }


# Обработчик для Telegram webhook (если нужен)
@app.post("/webhook/telegram", tags=["Webhook"])
async def telegram_webhook(request: Request):
    """Обработчик Telegram webhook"""
    try:
        update_data = await request.json()
        logger.info(f"📱 Получен Telegram update: {update_data.get('update_id')}")

        # TODO: Обработка через aiogram

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Webhook processing failed"}
        )


if __name__ == "__main__":
    import uvicorn

    logger.info("🔥 Запуск в режиме разработки")

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_config=None,  # Используем loguru вместо стандартного
        access_log=False   # Отключаем встроенное логирование
    )