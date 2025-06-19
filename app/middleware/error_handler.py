"""
Error Handler Middleware
Централизованная обработка ошибок
"""

import traceback
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from app.core.config import settings


def setup_error_handlers(app: FastAPI) -> None:
    """
    Настройка обработчиков ошибок для FastAPI

    Args:
        app: Экземпляр FastAPI
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Обработка HTTP ошибок"""

        logger.warning(
            f"🚨 HTTP {exc.status_code}: {exc.detail} | "
            f"Path: {request.url.path} | "
            f"Method: {request.method}"
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": "http_error",
                    "code": exc.status_code,
                    "message": exc.detail,
                    "path": str(request.url.path)
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Обработка ошибок валидации Pydantic"""

        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

        logger.warning(
            f"📋 Ошибка валидации: {len(errors)} полей | "
            f"Path: {request.url.path} | "
            f"Errors: {errors}"
        )

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "validation_error",
                    "code": 422,
                    "message": "Ошибка валидации данных",
                    "details": errors,
                    "path": str(request.url.path)
                }
            }
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """Обработка ошибок базы данных"""

        error_msg = "Ошибка базы данных"

        # Логируем полную ошибку
        logger.error(
            f"💾 Database Error: {str(exc)} | "
            f"Path: {request.url.path} | "
            f"Method: {request.method}"
        )

        # В режиме разработки показываем детали
        if settings.DEBUG:
            error_msg = str(exc)

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "database_error",
                    "code": 500,
                    "message": error_msg,
                    "path": str(request.url.path)
                }
            }
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Обработка ошибок значений"""

        logger.warning(
            f"⚠️ ValueError: {str(exc)} | "
            f"Path: {request.url.path}"
        )

        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "type": "value_error",
                    "code": 400,
                    "message": str(exc),
                    "path": str(request.url.path)
                }
            }
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(request: Request, exc: PermissionError):
        """Обработка ошибок доступа"""

        logger.warning(
            f"🔒 PermissionError: {str(exc)} | "
            f"Path: {request.url.path} | "
            f"User: {getattr(request.state, 'user_id', 'Anonymous')}"
        )

        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "type": "permission_error",
                    "code": 403,
                    "message": "Недостаточно прав доступа",
                    "path": str(request.url.path)
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Обработка всех остальных ошибок"""

        # Генерируем ID ошибки для отслеживания
        import uuid
        error_id = str(uuid.uuid4())[:8]

        # Подробное логирование
        logger.error(
            f"💥 Unhandled Exception [{error_id}]: {str(exc)} | "
            f"Path: {request.url.path} | "
            f"Method: {request.method} | "
            f"Type: {type(exc).__name__}"
        )

        # В режиме разработки показываем traceback
        if settings.DEBUG:
            logger.error(f"Traceback [{error_id}]:\n{traceback.format_exc()}")

        error_message = "Внутренняя ошибка сервера"
        if settings.DEBUG:
            error_message = f"{type(exc).__name__}: {str(exc)}"

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "code": 500,
                    "message": error_message,
                    "error_id": error_id,
                    "path": str(request.url.path)
                }
            }
        )

    logger.success("✅ Error handlers настроены")