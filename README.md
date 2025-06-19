# 🛍️ Telegram Marketplace Backend

Полнофункциональный backend для Telegram Mini App маркетплейса с поддержкой USDT и СБП платежей.

## 🚀 Особенности

- **FastAPI** - современный async веб-фреймворк
- **PostgreSQL** - надежная база данных с async поддержкой
- **SQLAlchemy 2.0** - ORM с полной типизацией
- **Alembic** - система миграций БД
- **Pydantic v2** - валидация и сериализация данных
- **Loguru** - красивое структурированное логирование
- **USDT платежи** - поддержка TRC-20, BEP-20, TON
- **СБП интеграция** - система быстрых платежей
- **СДЭК API** - интеграция доставки
- **Промокоды** - система скидок
- **Admin панель** - управление через API

## 📦 Структура проекта

```
telegram-marketplace/
├── app/
│   ├── api/                    # API эндпоинты
│   │   ├── dependencies/       # Зависимости (auth, db)
│   │   └── v1/endpoints/       # REST эндпоинты
│   ├── core/                   # Ядро приложения
│   │   ├── config.py          # Конфигурация
│   │   ├── database.py        # Подключение к БД
│   │   └── security.py        # Безопасность
│   ├── models/                 # SQLAlchemy модели
│   ├── schemas/                # Pydantic схемы
│   ├── services/               # Бизнес-логика
│   │   ├── telegram/          # Telegram бот
│   │   ├── payment/           # Платежные системы
│   │   ├── cdek/              # СДЭК доставка
│   │   └── blockchain/        # Блокчейн проверки
│   ├── utils/                  # Утилиты
│   └── main.py                 # Точка входа
├── alembic/                    # Миграции БД
├── logs/                       # Логи приложения
├── static/                     # Статические файлы
└── tests/                      # Тесты
```

## ⚙️ Быстрый старт

### 1. Клонирование и установка

```bash
git clone <repository-url>
cd telegram-marketplace
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. Настройка окружения

```bash
cp .env.example .env
# Отредактируйте .env файл с вашими настройками
```

### 3. Автоматическая настройка

```bash
python setup.py
```

Скрипт создаст необходимые директории, проверит конфигурацию и предложит создать миграции.

### 4. Запуск приложения

```bash
# Режим разработки
python -m app.main

# Или через uvicorn
uvicorn app.main:app --reload

# Документация API
http://localhost:8000/docs
```

## 🐳 Docker

### Запуск с Docker Compose

```bash
# Основные сервисы
docker-compose up -d

# С инструментами разработки (Adminer)
docker-compose --profile tools up -d

# Только база данных
docker-compose up -d postgres redis
```

### Сервисы

- **API**: http://localhost:8000
- **Документация**: http://localhost:8000/docs  
- **Adminer**: http://localhost:8080 (только с profile tools)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🗄️ База данных

### Модели данных

- **User** - пользователи Telegram
- **Product** - каталог товаров
- **Cart/CartItem** - корзина покупок
- **Order/OrderItem** - заказы
- **Promocode** - система промокодов
- **Payment** - платежи (USDT/СБП)
- **Delivery** - доставка (СДЭК)

### Миграции

```bash
# Создание миграции
alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

## 🔧 Конфигурация

### Основные настройки (.env)

```env
# База данных
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/marketplace_db

# Telegram Bot
BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id
ASSEMBLY_CHAT_ID=your_assembly_chat_id

# USDT кошельки
USDT_TRC20_WALLET=your_trc20_wallet
USDT_BEP20_WALLET=your_bep20_wallet  
USDT_TON_WALLET=your_ton_wallet

# Blockchain API
TRON_API_KEY=your_tron_api_key
BSC_API_KEY=your_bsc_api_key
TON_API_KEY=your_ton_api_key

# СДЭК
CDEK_CLIENT_ID=your_cdek_client_id
CDEK_CLIENT_SECRET=your_cdek_client_secret

# СБП
SBP_MERCHANT_ID=your_sbp_merchant_id
SBP_SECRET_KEY=your_sbp_secret_key
```

### Настройки маркетплейса

```env
# Доставка
FREE_DELIVERY_THRESHOLD=2000  # Бесплатная доставка от суммы
DELIVERY_COST=500             # Стоимость доставки

# Лимиты
PAYMENT_TIMEOUT_MINUTES=30    # Таймаут оплаты
LOW_STOCK_THRESHOLD=30        # Порог низкого остатка
```

## 📚 API Документация

### Основные эндпоинты

- **GET /api/v1/products** - каталог товаров
- **POST /api/v1/cart/items** - добавление в корзину
- **POST /api/v1/orders** - создание заказа
- **POST /api/v1/promocodes/validate** - проверка промокода
- **GET /api/v1/admin/stats** - статистика админа

### Аутентификация

Используется Telegram аутентификация через заголовки:

```
X-Telegram-User: {"id": 123456, "username": "user", ...}
```

## 🔄 Рабочий процесс

1. **Добавление в корзину** - товары добавляются в корзину пользователя
2. **Применение промокода** - проверка и применение скидки
3. **Оформление заказа** - указание контактов и адреса доставки
4. **Выбор оплаты** - USDT или СБП
5. **Автопроверка платежа** - мониторинг блокчейна/СБП
6. **Создание доставки** - интеграция с СДЭК
7. **Уведомления** - в Telegram о статусе заказа

## 📊 Логирование

Логи сохраняются в папке `logs/`:

- **app.log** - общие логи приложения
- **error.log** - ошибки
- **api.log** - HTTP запросы

### Настройка loguru

```python
from loguru import logger

logger.info("Информационное сообщение")
logger.error("Ошибка")
logger.success("Успешная операция")
```

## 🧪 Тестирование

```bash
# Запуск тестов
pytest

# С покрытием
pytest --cov=app

# Конкретный файл
pytest tests/test_products.py
```

## 🚀 Деплой

### Продакшн настройки

```env
DEBUG=false
ENVIRONMENT=production
```

### Systemd сервис

```ini
[Unit]
Description=Telegram Marketplace API
After=network.target

[Service]
Type=simple
User=marketplace
WorkingDirectory=/opt/telegram-marketplace
ExecStart=/opt/telegram-marketplace/venv/bin/python -m app.main
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📝 Разработка

### Добавление нового эндпоинта

1. Создать схему в `app/schemas/`
2. Добавить эндпоинт в `app/api/v1/endpoints/`
3. Реализовать логику в `app/services/`
4. Написать тесты в `tests/`

### Стиль кода

```bash
# Форматирование
black app/
isort app/

# Линтинг
flake8 app/
mypy app/
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature ветку
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл [LICENSE](LICENSE)

## 📞 Поддержка

При возникновении вопросов создайте Issue в репозитории.

---

**Разработано с ❤️ для Telegram маркетплейсов**