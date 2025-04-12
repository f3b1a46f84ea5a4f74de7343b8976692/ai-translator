FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов проекта
COPY requirements.txt .
COPY src/ src/
COPY main.py .

# Установка Python зависимостей
RUN pip3 install --no-cache-dir -r requirements.txt

# Создание директории для моделей
RUN mkdir -p models

# Копирование переменных окружения
COPY .env .env

# Запуск приложения
CMD ["python3", "main.py"] 