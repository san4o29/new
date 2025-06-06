import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт! Я твій Telegram-бот.")

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://yourdomain.com
    PORT = int(os.getenv("PORT", "8000"))

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=f"{WEBHOOK_URL}/webhook",
        webhook_path="/webhook",
    )

if __name__ == "__main__":
    main()
