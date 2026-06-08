# Wildberries Telegram Bot

Telegram-бот для работы с API Wildberries: товары, заказы, аналитика и финансы.

## Возможности

| Раздел | Команда | Что делает |
|---|---|---|
| 📦 Товары | Главное меню → Товары | Список товаров, остатки на складах, текущие цены |
| 📋 Заказы | Главное меню → Заказы | Новые заказы и продажи за 7 дней |
| 📊 Аналитика | Главное меню → Аналитика | Воронка продаж |
| 💰 Финансы | Главное меню → Финансы | Отчёт по реализации за 30 дней |
| 🔑 Аккаунты WB | Главное меню → Аккаунты WB | Добавление/удаление токенов WB API |

## Быстрый старт

### Локально

```bash
git clone https://github.com/ar1gel/re_hub.git
cd re_hub/wb_telegram_bot

# Виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Конфиг
cp .env.example .env
# Укажи BOT_TOKEN (получить у @BotFather)

# Запуск
python3 -m bot.main
```

### Docker

```bash
cp .env.example .env
# Укажи BOT_TOKEN в .env

docker compose up -d
docker compose logs -f
```

## Деплой на VPS

### Первый запуск (Ubuntu/Debian)

```bash
ssh user@ваш-сервер

# Скрипт установит Docker и скачает проект:
bash <(curl -s https://raw.githubusercontent.com/ar1gel/re_hub/master/wb_telegram_bot/setup_vps.sh)

# После создания .env — укажи токен бота:
nano re_hub/wb_telegram_bot/.env

# Запусти бота:
cd re_hub/wb_telegram_bot && sudo docker compose up -d
```

### Обновление после изменений в коде

```bash
./re_hub/wb_telegram_bot/update_vps.sh
# или:
bash <(curl -s https://raw.githubusercontent.com/ar1gel/re_hub/master/wb_telegram_bot/update_vps.sh)
```

Скрипт выполнит `git pull`, пересоберёт Docker-образ и перезапустит контейнер.

## Переменные окружения

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен Telegram-бота (получить у [@BotFather](https://t.me/BotFather)) |
| `DATABASE_URL` | URL для подключения к БД (по умолчанию SQLite) |

## Как получить токен WB API

1. Войти в [личный кабинет Wildberries](https://seller.wildberries.ru)
2. Настройки → Доступ к API
3. Создать новый токен с нужными правами
4. Добавить токен в бота через раздел «Аккаунты WB»

## Стек

- Python 3.12+
- [aiogram](https://aiogram.dev) 3.x — Telegram Bot API
- [wildberries-api](https://pypi.org/project/wildberries-api/) — клиент WB API
- SQLAlchemy + SQLite
- Docker
