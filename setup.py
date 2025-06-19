#!/usr/bin/env python3
"""
Скрипт настройки проекта
Инициализация alembic, создание папок, проверка зависимостей
"""

import os
import sys
import subprocess
from pathlib import Path


def create_directories():
    """Создание необходимых директорий"""
    directories = [
        "logs",
        "static/uploads",
        "alembic/versions",
        "tests",
        "docs"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Создана директория: {directory}")

    # Создание .gitkeep файлов
    gitkeep_dirs = [
        "logs/.gitkeep",
        "static/uploads/.gitkeep",
        "alembic/versions/.gitkeep"
    ]

    for gitkeep in gitkeep_dirs:
        Path(gitkeep).touch()
        print(f"✅ Создан файл: {gitkeep}")


def init_alembic():
    """Инициализация Alembic (если еще не инициализирован)"""
    if not Path("alembic/env.py").exists():
        print("⚠️ Alembic не инициализирован, инициализируем...")
        try:
            subprocess.run(["alembic", "init", "alembic"], check=True)
            print("✅ Alembic инициализирован")
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка инициализации Alembic: {e}")
            return False
    else:
        print("✅ Alembic уже инициализирован")

    return True


def check_env_file():
    """Проверка .env файла"""
    if not Path(".env").exists():
        print("⚠️ Файл .env не найден")
        if Path(".env.example").exists():
            print("📋 Скопируйте .env.example в .env и заполните настройки:")
            print("cp .env.example .env")
        return False
    else:
        print("✅ Файл .env найден")
    return True


def check_database_config():
    """Проверка настроек базы данных"""
    try:
        from app.core.config import settings
        print(f"✅ Конфигурация загружена")
        print(f"📊 Database URL: {str(settings.DATABASE_URL)[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False


def create_first_migration():
    """Создание первой миграции"""
    try:
        print("📊 Создание первой миграции...")
        subprocess.run([
            "alembic", "revision", "--autogenerate",
            "-m", "Initial migration: create all tables"
        ], check=True)
        print("✅ Первая миграция создана")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка создания миграции: {e}")
        return False


def run_migrations():
    """Применение миграций"""
    try:
        print("📊 Применение миграций...")
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("✅ Миграции применены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка применения миграций: {e}")
        return False


def test_import():
    """Тестирование импорта основных модулей"""
    try:
        print("🧪 Тестирование импортов...")

        from app.core.config import settings
        print("✅ Конфигурация импортирована")

        from app.core.database import Base
        print("✅ База данных импортирована")

        from app.db.base import *
        print("✅ Модели импортированы")

        from app.main import app
        print("✅ FastAPI приложение импортировано")

        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False


def main():
    """Основная функция настройки"""
    print("🚀 Настройка Telegram Marketplace")
    print("=" * 50)

    # Создание директорий
    print("\n📁 Создание директорий...")
    create_directories()

    # Проверка .env файла
    print("\n⚙️ Проверка конфигурации...")
    if not check_env_file():
        print("❌ Настройте .env файл перед продолжением")
        return False

    # Проверка конфигурации БД
    if not check_database_config():
        print("❌ Ошибка конфигурации базы данных")
        return False

    # Тестирование импортов
    print("\n🧪 Тестирование модулей...")
    if not test_import():
        print("❌ Ошибка в модулях")
        return False

    # Создание миграции
    print("\n📊 Настройка базы данных...")
    create_migration = input("Создать миграцию? (y/n): ").lower() == 'y'
    if create_migration:
        if create_first_migration():
            apply_migration = input("Применить миграцию? (y/n): ").lower() == 'y'
            if apply_migration:
                run_migrations()

    print("\n" + "=" * 50)
    print("✅ Настройка завершена!")
    print("\n📋 Следующие шаги:")
    print("1. Заполните настройки в .env файле")
    print("2. Запустите сервер: python -m app.main")
    print("3. Или через uvicorn: uvicorn app.main:app --reload")
    print("4. Документация API: http://localhost:8000/docs")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)