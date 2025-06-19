"""
Конфигурация приложения
Все настройки загружаются из переменных окружения
"""

from typing import Optional, List
from pydantic import field_validator, PostgresDsn
from pydantic_settings import BaseSettings
from pydantic.networks import AnyHttpUrl
import secrets


class Settings(BaseSettings):
    """Основные настройки приложения"""

    # Основные настройки
    PROJECT_NAME: str = "Telegram Marketplace"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Безопасность
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 дней

    # Сервер
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # База данных
    DATABASE_URL: Optional[PostgresDsn] = None
    DATABASE_URL_SYNC: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v):
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user="user",
            password="password",
            host="localhost",
            port="5432",
            path="/marketplace_db"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True


class TelegramSettings(BaseSettings):
    """Настройки Telegram бота"""

    BOT_TOKEN: str
    WEBHOOK_URL: Optional[str] = None
    ADMIN_CHAT_ID: Optional[int] = None
    ASSEMBLY_CHAT_ID: Optional[int] = None

    # Лимиты Telegram
    MAX_MESSAGE_LENGTH: int = 4096
    MAX_CAPTION_LENGTH: int = 1024

    class Config:
        env_prefix = "TELEGRAM_"
        env_file = ".env"


class PaymentSettings(BaseSettings):
    """Настройки платежных систем"""

    # USDT кошельки
    USDT_TRC20_WALLET: str
    USDT_BEP20_WALLET: str
    USDT_TON_WALLET: str

    # Blockchain API ключи
    TRON_API_KEY: str
    BSC_API_KEY: str
    TON_API_KEY: str

    # СБП настройки
    SBP_MERCHANT_ID: str
    SBP_SECRET_KEY: str
    SBP_TEST_MODE: bool = True

    # Таймауты и лимиты
    PAYMENT_TIMEOUT_MINUTES: int = 30
    MIN_USDT_AMOUNT: float = 1.0
    MAX_USDT_AMOUNT: float = 10000.0

    class Config:
        env_file = ".env"


class CDEKSettings(BaseSettings):
    """Настройки СДЭК API"""

    CLIENT_ID: str
    CLIENT_SECRET: str
    TEST_MODE: bool = True

    # URLs для API
    @property
    def base_url(self) -> str:
        if self.TEST_MODE:
            return "https://api.edu.cdek.ru/v2"
        return "https://api.cdek.ru/v2"

    @property
    def auth_url(self) -> str:
        return f"{self.base_url}/oauth/token"

    @property
    def calculate_url(self) -> str:
        return f"{self.base_url}/calculator/tarifflist"

    @property
    def order_url(self) -> str:
        return f"{self.base_url}/orders"

    class Config:
        env_prefix = "CDEK_"
        env_file = ".env"


class MarketplaceSettings(BaseSettings):
    """Настройки маркетплейса"""

    # Доставка
    FREE_DELIVERY_THRESHOLD: int = 2000  # Бесплатная доставка от суммы
    DELIVERY_COST: int = 500  # Стоимость доставки

    # Лимиты товаров
    LOW_STOCK_THRESHOLD: int = 30  # Порог для уведомления о низком остатке
    MAX_CART_ITEMS: int = 50  # Максимум товаров в корзине
    MAX_ITEM_QUANTITY: int = 99  # Максимум одного товара

    # Промокоды
    MAX_PROMOCODE_DISCOUNT: int = 90  # Максимальная скидка в %
    MIN_PROMOCODE_LENGTH: int = 3
    MAX_PROMOCODE_LENGTH: int = 20

    # Файлы
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_PATH: str = "static/uploads"
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]

    class Config:
        env_file = ".env"


class RedisSettings(BaseSettings):
    """Настройки Redis"""

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_EXPIRE_SECONDS: int = 3600  # 1 час

    # Префиксы для ключей
    CART_PREFIX: str = "cart:"
    SESSION_PREFIX: str = "session:"
    PAYMENT_PREFIX: str = "payment:"
    RATE_LIMIT_PREFIX: str = "rate_limit:"

    class Config:
        env_file = ".env"


# Создание экземпляров настроек
settings = Settings()
telegram_settings = TelegramSettings()
payment_settings = PaymentSettings()
cdek_settings = CDEKSettings()
marketplace_settings = MarketplaceSettings()
redis_settings = RedisSettings()