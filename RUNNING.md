# Запуск проекта

## Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Telegram Bot Token (получить через [@BotFather](https://t.me/BotFather))

## Настройка

```bash
cp .env.example .env
```

Открыть `.env` и добавить токен бота:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Запуск

```bash
docker-compose up --build
```

Первый запуск занимает несколько минут (сборка образов).

## Сервисы

| Сервис | Адрес |
|--------|-------|
| User Service API | http://localhost:8000 |
| Rating Service API | http://localhost:8001 |
| Match Service API | http://localhost:8002 |
| RabbitMQ Management UI | http://localhost:15672 (guest / guest) |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

## Остановка

```bash
docker-compose down
```

Остановка с удалением данных:

```bash
docker-compose down -v
```

## Локальная разработка (без Docker)

Поднять инфраструктуру отдельно:

```bash
docker-compose up postgres rabbitmq redis
```

Затем запустить сервисы вручную, предварительно настроив переменные окружения согласно `.env.example`.
