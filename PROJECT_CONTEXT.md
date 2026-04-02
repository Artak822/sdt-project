# 📋 Dating Bot — Project Context

> **Последнее обновление:** 16 марта 2026 г.  
> **Статус:** 🟡 Планирование / Проектирование

---

## 🎯 Описание проекта

Telegram-бот для знакомств с системой рейтинга, кэшированием и асинхронной обработкой событий.

**Основной функционал:**
- Регистрация пользователей через Telegram
- Создание и редактирование анкет
- Просмотр анкет других пользователей (свайп-механика)
- Система лайков и мэтчей
- Рейтинговая система (3 уровня)
- Уведомления о новых событиях

---

## 🏗 Архитектура системы

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAILWAY (Cloud)                          │
│                                                                 │
│  ┌─────────────────┐                                           │
│  │  Telegram Bot   │  (Aiogram 3.x)                            │
│  │  - Интерфейс    │                                           │
│  │  - Регистрация  │                                           │
│  │  - Анкеты       │                                           │
│  └────────┬────────┘                                           │
│           │ Публикует события                                  │
│           ▼                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    RabbitMQ                              │   │
│  │  Exchanges: dating.exchange                              │   │
│  │  Queues: likes_queue, matches_queue, register_queue      │   │
│  └─────────────────────────────────────────────────────────┘   │
│           │                                                     │
│           │ Подписываются                                       │
│           ▼                                                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │  Rating Service │  │  Match Service  │  │  User Service  │  │
│  │   (FastAPI)     │  │   (FastAPI)     │  │   (FastAPI)    │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬───────┘  │
│           │                    │                    │           │
│           └────────────────────┼────────────────────┘           │
│                                ▼                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   PostgreSQL                             │   │
│  │  Tables: users, profiles, likes, matches, ratings        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Redis                               │   │
│  │  - Кэш анкет (session queues)                           │   │
│  │  - Сессии пользователей                                 │   │
│  │  - Celery broker & backend                              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     Celery                               │   │
│  │  - Пересчёт рейтингов (периодически)                    │   │
│  │  - Фоновые задачи                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
              ┌─────────────────────────────────┐
              │  Cloudflare R2 / AWS S3         │
              │  - Хранение фотографий           │
              └─────────────────────────────────┘
```

---

## 🛠 Технологический стек

| Компонент | Технология | Версия | Назначение |
|-----------|------------|--------|------------|
| **Бот** | Aiogram | 3.x | Telegram Bot API |
| **API** | FastAPI | 0.100+ | REST API, бизнес-логика |
| **БД** | PostgreSQL | 15+ | Основное хранилище данных |
| **Кэш** | Redis | 7+ | Кэширование, сессии, Celery |
| **MQ** | RabbitMQ | 3.11+ | Очереди сообщений |
| **Tasks** | Celery | 5.x | Фоновые задачи |
| **Storage** | Cloudflare R2 / Minio | — | Хранение фото |
| **Deploy** | Railway | — | Хостинг всех сервисов |
| **Language** | Python | 3.11+ | Основной язык |

---

## 🗄 Структура базы данных

### Таблица: `users`
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | BIGINT | Telegram ID (PK) |
| `username` | VARCHAR | Username Telegram |
| `created_at` | TIMESTAMP | Дата регистрации |
| `last_active` | TIMESTAMP | Последняя активность |
| `is_banned` | BOOLEAN | Забанен ли |

### Таблица: `profiles`
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Уникальный ID профиля |
| `user_id` | BIGINT | Ссылка на users (FK) |
| `name` | VARCHAR | Имя |
| `age` | INTEGER | Возраст |
| `gender` | ENUM | Пол (male/female/other) |
| `bio` | TEXT | Описание |
| `city` | VARCHAR | Город |
| `latitude` | DECIMAL | Широта |
| `longitude` | DECIMAL | Долгота |
| `looking_for` | ENUM | Кого ищет (male/female/both) |
| `age_range_min` | INTEGER | Мин. возраст |
| `age_range_max` | INTEGER | Макс. возраст |
| `is_complete` | BOOLEAN | Заполнена ли анкета |
| `updated_at` | TIMESTAMP | Последнее обновление |

### Таблица: `profile_photos`
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Уникальный ID |
| `profile_id` | UUID | Ссылка на profiles (FK) |
| `s3_key` | VARCHAR | Ключ в S3 хранилище |
| `s3_url` | VARCHAR | Публичная ссылка |
| `is_primary` | BOOLEAN | Главное фото |
| `order` | INTEGER | Порядок сортировки |

### Таблица: `likes`
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Уникальный ID |
| `from_user_id` | BIGINT | Кто лайкнул |
| `to_user_id` | BIGINT | Кого лайкнули |
| `created_at` | TIMESTAMP | Дата лайка |
| `is_mutual` | BOOLEAN | Взаимный ли (мэтч) |

### Таблица: `matches`
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Уникальный ID |
| `user1_id` | BIGINT | Первый пользователь |
| `user2_id` | BIGINT | Второй пользователь |
| `created_at` | TIMESTAMP | Дата мэтча |
| `chat_started` | BOOLEAN | Начат ли диалог |

### Таблица: `ratings`
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | UUID | Уникальный ID |
| `profile_id` | UUID | Ссылка на profiles (FK) |
| `primary_score` | DECIMAL | Первичный рейтинг |
| `behavioral_score` | DECIMAL | Поведенческий рейтинг |
| `combined_score` | DECIMAL | Итоговый рейтинг |
| `calculated_at` | TIMESTAMP | Дата расчёта |

### Таблица: `interests` (справочник)
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INTEGER | Уникальный ID |
| `name` | VARCHAR | Название интереса |

### Талица: `profile_interests` (связь M:M)
| Поле | Тип | Описание |
|------|-----|----------|
| `profile_id` | UUID | Ссылка на profiles |
| `interest_id` | INTEGER | Ссылка на interests |

---

## 📬 RabbitMQ — Топики и Очереди

### Exchange: `dating.exchange` (Direct)

| Routing Key | Queue | Consumer | Описание |
|-------------|-------|----------|----------|
| `user.register` | `register_queue` | User Service | Регистрация нового пользователя |
| `user.profile.complete` | `profile_complete_queue` | Rating Service | Анкета заполнена |
| `user.like` | `likes_queue` | Rating Service, Match Service | Поставлен лайк |
| `user.match` | `matches_queue` | Notification Service | Образовался мэтч |
| `user.session.start` | `session_queue` | Cache Service | Начата сессия (загрузка кэша) |

### Формат сообщений (JSON)

```json
// user.register
{
  "event": "user.register",
  "timestamp": "2026-03-16T10:00:00Z",
  "data": {
    "user_id": 123456789,
    "username": "@username"
  }
}

// user.like
{
  "event": "user.like",
  "timestamp": "2026-03-16T10:05:00Z",
  "data": {
    "from_user_id": 123456789,
    "to_user_id": 987654321,
    "to_profile_id": "uuid-here"
  }
}

// user.match
{
  "event": "user.match",
  "timestamp": "2026-03-16T10:10:00Z",
  "data": {
    "user1_id": 123456789,
    "user2_id": 987654321,
    "match_id": "match-uuid-here"
  }
}
```

---

## 📊 Система рейтинга

### Уровень 1: Первичный рейтинг (0-100)

```
primary_score = 
  completeness_bonus (0-40) +     // Полнота анкеты
  photos_bonus (0-20) +           // Количество фото
  preferences_match (0-40)        // Совпадение предпочтений
```

| Фактор | Макс. баллы | Как считается |
|--------|-------------|---------------|
| Заполненность анкеты | 40 | % заполненных полей |
| Количество фото | 20 | 1 фото = 5 баллов, макс 4 фото |
| Совпадение предпочтений | 40 | Возраст, пол, город |

### Уровень 2: Поведенческий рейтинг (0-100)

```
behavioral_score =
  likes_received (0-30) +       // Полученные лайки
  like_ratio (0-25) +           // Соотношение лайков/пропусков
  matches_count (0-25) +        // Количество мэтчей
  chat_initiated (0-20)         // Начатые диалоги
```

| Фактор | Макс. баллы | Как считается |
|--------|-------------|---------------|
| Полученные лайки | 30 | Нормализованное количество |
| Соотношение лайков | 25 | likes / (likes + passes) |
| Мэтчи | 25 | Количество взаимных лайков |
| Диалоги | 20 | % мэтчей с начатым диалогом |

### Уровень 3: Комбинированный рейтинг

```
combined_score = 
  primary_score * 0.4 +         // 40% первичный
  behavioral_score * 0.5 +      // 50% поведенческий
  referral_bonus * 0.1          // 10% рефералы
```

### Пересчёт рейтинга (Celery)

| Задача | Период | Описание |
|--------|--------|----------|
| `recalculate_behavioral_rating` | Каждые 10 мин | Пересчёт поведенческого рейтинга |
| `recalculate_combined_rating` | Каждый час | Полный пересчёт |
| `cleanup_old_sessions` | Каждый день | Очистка старых сессий в Redis |

---

## 🔑 Redis — Структура ключей

### Кэш анкет (Session Queue)

```
Pattern: session:{user_id}:queue
Type: List
TTL: 30 минут
Содержимое: [profile_id_1, profile_id_2, ..., profile_id_10]
```

### Предрассчитанные анкеты

```
Pattern: profile:{profile_id}:data
Type: Hash
TTL: 1 час
Содержимое: {name, age, bio, photos..., rating}
```

### Активные сессии

```
Pattern: session:{user_id}:active
Type: String
TTL: 30 минут
Содержимое: "true"
```

### Счётчики для рейтинга

```
Pattern: stats:likes:{user_id}
Type: String
Содержимое: количество лайков

Pattern: stats:matches:{user_id}
Type: String
Содержимое: количество мэтчей
```

---

## 📁 Структура проекта

```
dating-bot/
├── README.md                    # Документация
├── PROJECT_CONTEXT.md           # Этот файл
├── docker-compose.yml           # Локальная разработка
│
├── bot/                         # Telegram бот (Aiogram)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                  # Точка входа
│   ├── config.py                # Конфигурация
│   ├── handlers/                # Обработчики
│   │   ├── __init__.py
│   │   ├── start.py             # /start, регистрация
│   │   ├── profile.py           # /profile, анкета
│   │   ├── search.py            # /search, просмотр
│   │   └── menu.py              # Главное меню
│   ├── keyboards/               # Клавиатуры
│   │   ├── inline.py            # Inline-кнопки
│   │   └── reply.py             # Reply-кнопки
│   └── fsm/                     # Машина состояний
│       └── states.py            # Состояния для заполнения анкеты
│
├── services/                    # Микросервисы (FastAPI)
│   ├── user_service/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── crud.py
│   │   └── rabbitmq.py          # Producer/Consumer
│   │
│   ├── rating_service/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── algorithms.py        # Алгоритмы рейтинга
│   │   └── rabbitmq.py
│   │
│   └── match_service/
│       ├── Dockerfile
│       ├── main.py
│       ├── logic.py
│       └── rabbitmq.py
│
├── celery_worker/               # Фоновые задачи
│   ├── Dockerfile
│   ├── tasks.py                 # Celery tasks
│   └── celery_app.py
│
├── migrations/                  # Миграции БД (Alembic)
│   └── versions/
│
└── tests/                       # Тесты
    ├── test_bot.py
    ├── test_services.py
    └── test_rating.py
```

---

## 🚀 Статус разработки

### Этап 1: Планирование и проектирование 🟡 (В ПРОЦЕССЕ)

| Задача | Статус | Описание |
|--------|--------|----------|
| Описание сервисов | 🟡 | Определение границ сервисов |
| Архитектура системы | 🟢 | Схема нарисована |
| Схема данных в БД | 🟢 | Таблицы спроектированы |
| Git репозиторий | 🔴 | Не создан |

### Этап 2: Разработка базовой функциональности 🔴 (НЕ НАЧАТО)

| Задача | Статус | Описание |
|--------|--------|----------|
| Написание бота | 🔴 | Aiogram, интерфейс |
| Регистрация пользователей | 🔴 | /start команда |
| Подключение к Railway | 🔴 | Деплой базовый |

### Этап 3: Система анкет и ранжирования 🔴 (НЕ НАЧАТО)

| Задача | Статус | Описание |
|--------|--------|----------|
| CRUD для анкет | 🔴 | Создание, чтение, обновление, удаление |
| Алгоритм рейтинга | 🔴 | Минимум 1 из каждого уровня |
| Redis кэширование | 🔴 | Кэш анкет в сессии |
| Интеграция с ботом | 🔴 | Через RabbitMQ |

### Этап 4: Дополнительные функции 🔴 (НЕ НАЧАТО)

| Задача | Статус | Описание |
|--------|--------|----------|
| Celery задачи | 🔴 | Пересчёт рейтингов |
| Оптимизация БД | 🔴 | Индексы, запросы |
| Тестирование | 🔴 | Unit, integration |
| Деплой | 🔴 | Production на Railway |

---

## 📈 Метрики и логирование

### Метрики (для сбора статистики)

| Метрика | Где собирать | Описание |
|---------|--------------|----------|
| `users.registered_total` | User Service | Всего зарегистрировано |
| `profiles.completed_total` | User Service | Всего заполнено анкет |
| `likes.sent_total` | Match Service | Всего отправлено лайков |
| `matches.created_total` | Match Service | Всего создано мэтчей |
| `sessions.active_current` | Redis | Активных сессий сейчас |
| `rating.recalculate_duration` | Celery | Время пересчёта рейтинга |

### Логирование

| Уровень | Когда используется |
|---------|-------------------|
| DEBUG | Отладочная информация (разработка) |
| INFO | Обычные события (регистрация, лайк, мэтч) |
| WARNING | Предупреждения (повторные попытки, кэш-мисс) |
| ERROR | Ошибки (БД недоступна, MQ упала) |
| CRITICAL | Критические ошибки (сервис не запускается) |

---

## 🔐 Переменные окружения

### Для бота (`bot/.env`)

```env
TELEGRAM_BOT_TOKEN=your_bot_token
RABBITMQ_URL=amqp://user:pass@host:5672
LOG_LEVEL=INFO
```

### Для сервисов (`services/*/.env`)

```env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
REDIS_URL=redis://user:pass@host:6379/0
RABBITMQ_URL=amqp://user:pass@host:5672
S3_ENDPOINT_URL=https://your-endpoint.r2.cloudflarestorage.com
S3_ACCESS_KEY=your_access_key
S3_SECRET_KEY=your_secret_key
S3_BUCKET=your_bucket_name
LOG_LEVEL=INFO
```

### Для Celery (`celery_worker/.env`)

```env
CELERY_BROKER_URL=redis://user:pass@host:6379/1
CELERY_RESULT_BACKEND=redis://user:pass@host:6379/2
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

---

## 🎯 Фишки проекта (для высокой оценки)

| Фишка | Описание | Статус |
|-------|----------|--------|
| **Слепое свидание** | Анонимный чат до раскрытия фото | 🔴 |
| **Избранное** | Сохранение понравившихся анкет | 🔴 |
| **Чёрный список** | Блокировка нежелательных пользователей | 🔴 |
| **Верификация фото** | Проверка на соответствие описанию | 🔴 |
| **Реферальная система** | Бонусы за приглашённых друзей | 🔴 |
| **Ачивки** | Достижения за активность | 🔴 |
| **Статистика профиля** | Показывать пользователю его метрики | 🔴 |

---

## 📝 Глоссарий

| Термин | Значение |
|--------|----------|
| **Мэтч (Match)** | Взаимный лайк между двумя пользователями |
| **Лайк (Like)** | Симпатия к анкете другого пользователя |
| **Свайп (Swipe)** | Действие просмотра анкеты (лайк/пропуск) |
| **Сессия (Session)** | Период активности пользователя в боте |
| **Первичный рейтинг** | Статический рейтинг на основе данных анкеты |
| **Поведенческий рейтинг** | Динамический рейтинг на основе активности |
| **Комбинированный рейтинг** | Итоговый рейтинг (весовая модель) |

---

## 🔗 Полезные ссылки

- [Aiogram Documentation](https://docs.aiogram.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Railway Documentation](https://docs.railway.app/)

---

## 📞 Контакты и ресурсы

| Ресурс | Ссылка |
|--------|--------|
| Git Repository | _будет создан_ |
| Railway Project | _будет развёрнут_ |
| Telegram Bot | _будет создан_ |

---

> **Примечание:** Этот документ следует обновлять после каждого значимого изменения в проекте.
