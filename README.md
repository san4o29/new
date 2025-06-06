# Telegram Bot (Webhook Version)

Цей бот використовує Webhook для взаємодії з Telegram API. Працює на Railway або Render.

## 🔧 Змінні середовища

- `BOT_TOKEN` – токен від BotFather
- `WEBHOOK_URL` – публічна адреса Railway/Render (наприклад: https://mybot.up.railway.app)
- `PORT` – (не обов'язково) порт для запуску, за замовчуванням 8000

## 🚀 Деплой на Railway

1. Форкни або завантаж репозиторій
2. Перейди на [https://railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Додай змінні середовища у вкладці **Settings → Variables**
4. Railway автоматично запустить бот

## 🛡 Переваги Webhook

- Немає помилки `Conflict: terminated by other getUpdates request`
- Реакція на події швидша
- Менше витрат ресурсів
