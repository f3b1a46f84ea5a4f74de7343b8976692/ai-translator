# Telegram Voice Translation Bot

Бот для перевода голосовых и текстовых сообщений на русский язык с последующим озвучиванием.

## Требования

- Python 3.10+
- CUDA 12.1+ (для GPU)
- Docker и Docker Compose (опционально)

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd travel_bot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/Mac
venv\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

5. Отредактируйте `.env` и укажите ваш токен бота:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Запуск

### Локально

```bash
python main.py
```

### В Docker

1. Убедитесь, что установлен NVIDIA Container Toolkit:
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
   && curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add - \
   && curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

2. Соберите и запустите контейнер:
```bash
docker-compose up -d
```

## Структура проекта

```
.
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   └── handlers.py
│   ├── services/
│   │   ├── transcription.py
│   │   ├── translation.py
│   │   └── speech.py
│   ├── __init__.py
│   └── config.py
├── models/
├── main.py
├── requirements.txt
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

## Использование

1. Отправьте боту текстовое сообщение на любом языке
2. Отправьте боту голосовое сообщение на любом языке
3. Бот распознает текст, переведет его на русский и озвучит

## Лицензия

MIT 