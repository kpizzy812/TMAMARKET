# Базовый образ Python
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN groupadd -r marketplace && useradd -r -g marketplace marketplace

# Установка рабочей директории
WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p logs static/uploads alembic/versions

# Установка прав доступа
RUN chown -R marketplace:marketplace /app

# Переключение на пользователя marketplace
USER marketplace

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Открытие порта
EXPOSE 8000

# Команда запуска
CMD ["python", "-m", "app.main"]