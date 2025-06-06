import os
import logging
from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from langdetect import detect

# Логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Змінні середовища
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ініціалізація OpenAI клієнта
client = OpenAI(api_key=OPENAI_API_KEY)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["/start", "Допомога"], ["Що таке karta pobytu?"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "Привіт! Я бот для допомоги з легалізацією в Польщі 🇵🇱\nНапиши своє питання!",
        reply_markup=reply_markup
    )

# Визначення мови
def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

# Обробка повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.message.from_user.id
    lang = detect_language(user_message)

    logging.info(f"User {user_id} ({lang}): {user_message}")

    prompt = f"Користувач питає про легалізацію в Польщі. Відповідай простою мовою.\nПитання: {user_message}"

    try:
        response = client.chat.completions.create(
    model="gpt-3.5-turbo",  # або gpt-4, якщо маєш доступ
    messages=[
        {"role": "system", "content": "Ти експерт із легалізації в Польщі."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=500
)
answer = response.choices[0].message.content
        await update.message.reply_text(answer)

    except Exception as e:
        logging.error(f"OpenAI error: {e}")
        await update.message.reply_text("Виникла помилка при отриманні відповіді. Спробуйте пізніше.")

# Запуск webhook
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
