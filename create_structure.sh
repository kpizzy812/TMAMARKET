#!/bin/bash

# Создание основной структуры проекта
mkdir -p {app,tests,docs,static}

# Backend структура
mkdir -p app/{api,core,models,schemas,services,utils,middleware}
mkdir -p app/api/{v1,dependencies}
mkdir -p app/api/v1/{endpoints,auth}
mkdir -p app/core/{config,security}
mkdir -p app/services/{telegram,payment,cdek,blockchain}
mkdir -p app/utils/{validators,helpers}

# Database
mkdir -p app/db/{migrations,seeds}

# Static files
mkdir -p static/{images,uploads}

# Создание основных файлов
touch app/__init__.py
touch app/main.py
touch app/api/__init__.py
touch app/api/dependencies/__init__.py
touch app/api/dependencies/auth.py
touch app/api/dependencies/database.py
touch app/api/v1/__init__.py
touch app/api/v1/api.py

# API endpoints
touch app/api/v1/endpoints/__init__.py
touch app/api/v1/endpoints/products.py
touch app/api/v1/endpoints/orders.py
touch app/api/v1/endpoints/users.py
touch app/api/v1/endpoints/cart.py
touch app/api/v1/endpoints/promocodes.py
touch app/api/v1/endpoints/admin.py
touch app/api/v1/endpoints/webhook.py

# Core
touch app/core/__init__.py
touch app/core/config.py
touch app/core/database.py
touch app/core/security.py

# Models
touch app/models/__init__.py
touch app/models/user.py
touch app/models/product.py
touch app/models/order.py
touch app/models/cart.py
touch app/models/promocode.py
touch app/models/payment.py
touch app/models/delivery.py

# Schemas (Pydantic)
touch app/schemas/__init__.py
touch app/schemas/user.py
touch app/schemas/product.py
touch app/schemas/order.py
touch app/schemas/cart.py
touch app/schemas/promocode.py
touch app/schemas/payment.py
touch app/schemas/admin.py

# Services
touch app/services/__init__.py
touch app/services/product_service.py
touch app/services/order_service.py
touch app/services/cart_service.py
touch app/services/promocode_service.py
touch app/services/user_service.py
touch app/services/admin_service.py

# Payment services
touch app/services/payment/__init__.py
touch app/services/payment/usdt_service.py
touch app/services/payment/sbp_service.py
touch app/services/payment/payment_checker.py

# Telegram services
touch app/services/telegram/__init__.py
touch app/services/telegram/bot_service.py
touch app/services/telegram/webhook_handler.py
touch app/services/telegram/message_service.py

# CDEK service
touch app/services/cdek/__init__.py
touch app/services/cdek/cdek_service.py
touch app/services/cdek/tracking_service.py

# Blockchain services
touch app/services/blockchain/__init__.py
touch app/services/blockchain/ton_checker.py
touch app/services/blockchain/bep20_checker.py
touch app/services/blockchain/trc20_checker.py

# Utils
touch app/utils/__init__.py
touch app/utils/validators.py
touch app/utils/helpers.py
touch app/utils/file_utils.py
touch app/utils/crypto_utils.py

# Middleware
touch app/middleware/__init__.py
touch app/middleware/cors.py
touch app/middleware/error_handler.py

# Database
touch app/db/__init__.py
touch app/db/base.py
touch app/db/session.py

# Root files
touch .env
touch .env.example
touch requirements.txt
touch alembic.ini
touch Dockerfile
touch docker-compose.yml
touch README.md

echo "Структура проекта создана успешно!"
echo "Не забудьте:"
echo "1. Заполнить .env файл"
echo "2. Установить зависимости: pip install -r requirements.txt"
echo "3. Инициализировать alembic: alembic init app/db/migrations"