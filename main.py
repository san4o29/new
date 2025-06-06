import os
import logging
from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, ConversationHandler, filters, CallbackQueryHandler
)
from langdetect import detect
from openai import OpenAI

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Состояния для ConversationHandler
SELECT_COUNTRY, SELECT_LANGUAGE, HANDLE_QUESTION, FEEDBACK = range(4)

# Инициализация OpenAI клиента
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Поддерживаемые страны и языки
COUNTRIES = ["Україна", "Білорусь", "Молдова", "Грузія", "Індонезія", "Колумбія", "Філіппіни", "Непал"]
LANGUAGES = {
    "uk": "Українська",
    "ru": "Російська",
    "pl": "Польська",
    "en": "Англійська",
    "es": "Іспанська",
    "id": "Індонезійська"
}

# Расширенная офлайн база FAQ (пример, добавил es и id)
offline_faq = {
    "україна": {
        "uk": {
            "як отримати карту побиту?": "Карту побиту можна отримати через подачу документів до воєводського управління...",
            "які документи потрібні для легалізації?": "Потрібно надати паспорт, дозвіл на роботу, підтвердження житла...",
        },
        "ru": {
            "как получить карту побыту?": "Карту побыту можно получить подав документы в воеводское управление...",
            "какие документы нужны для легализации?": "Нужно предоставить паспорт, разрешение на работу, подтверждение жилья...",
        },
        "pl": {
            "jak otrzymać kartę pobytu?": "Kartę pobytu można otrzymać poprzez złożenie dokumentów do urzędu wojewódzkiego...",
            "jakie dokumenty są potrzebne do legalizacji?": "Należy przedstawić paszport, pozwolenie na pracę, potwierdzenie miejsca zamieszkania...",
        },
        "en": {
            "how to get a residence card?": "You can get a residence card by submitting documents to the voivodeship office...",
            "what documents are needed for legalization?": "You need to provide a passport, work permit, proof of accommodation...",
        },
        "es": {
            "¿cómo obtener una tarjeta de residencia?": "Puede obtener una tarjeta de residencia presentando documentos en la oficina de la voivodía...",
            "¿qué documentos se necesitan para la legalización?": "Necesita presentar pasaporte, permiso de trabajo, comprobante de alojamiento...",
        },
        "id": {
            "bagaimana cara mendapatkan kartu tinggal?": "Anda dapat memperoleh kartu tinggal dengan menyerahkan dokumen ke kantor wojewódzki...",
            "dokumen apa saja yang diperlukan untuk legalisasi?": "Anda perlu menyerahkan paspor, izin kerja, bukti tempat tinggal...",
        }
    },
    # Другие страны можно добавить аналогично
}

# Поиск ответа в FAQ
def find_answer(country_key, lang_key, question_text):
    country_data = offline_faq.get(country_key.lower())
    if not country_data:
        return None
    lang_data = country_data.get(lang_key)
    if not lang_data:
        return None
    q = question_text.lower()
    for known_question, answer in lang_data.items():
        if known_question in q:
            return answer
    return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton(country)] for country in COUNTRIES]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Виберіть, будь ласка, вашу країну:",
        reply_markup=reply_markup
    )
    return SELECT_COUNTRY

async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_country = update.message.text
    if selected_country not in COUNTRIES:
        await update.message.reply_text("Будь ласка, виберіть країну зі списку.")
        return SELECT_COUNTRY
    context.user_data['country'] = selected_country.lower()

    keyboard = [[KeyboardButton(name)] for code, name in LANGUAGES.items()]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text(
        "Оберіть мову спілкування / Choose your language:",
        reply_markup=reply_markup
    )
    return SELECT_LANGUAGE

async def select_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_language = update.message.text
    lang_code = None
    for code, name in LANGUAGES.items():
        if name.lower() == selected_language.lower():
            lang_code = code
            break
    if not lang_code:
        await update.message.reply_text("Будь ласка, виберіть мову зі списку.")
        return SELECT_LANGUAGE
    context.user_data['language'] = lang_code

    # Добавляем кнопку обратной связи в меню
    keyboard = [
        [KeyboardButton("Задати питання")],
        [KeyboardButton("Залишити відгук")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"Ви обрали країну: {context.user_data['country'].capitalize()} та мову: {selected_language}.\n"
        "Ви можете задати питання про легалізацію або залишити відгук.",
        reply_markup=reply_markup
    )
    return HANDLE_QUESTION

# Обработка выбора из главного меню (вопрос или отзыв)
async def handle_question_or_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text in ["залишити відгук", "оставить отзыв", "leave feedback", "berikan umpan balik", "dejar comentarios"]:
        await update.message.reply_text(
            "Будь ласка, напишіть ваш відгук або пропозицію:",
            reply_markup=ReplyKeyboardRemove()
        )
        return FEEDBACK
    elif text in ["задати питання", "задать вопрос", "ask a question", "tanyakan pertanyaan", "hacer una pregunta"]:
        await update.message.reply_text(
            "Будь ласка, поставте ваше питання:",
            reply_markup=ReplyKeyboardRemove()
        )
        return HANDLE_QUESTION
    else:
        # Обрабатываем как вопрос по умолчанию
        return await handle_question(update, context)

async def handle_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    user_lang = detect(user_text)
    country = context.user_data.get('country')
    if not country:
        await update.message.reply_text("Спочатку виберіть країну командою /start")
        return ConversationHandler.END

    # Сначала пытаемся найти офлайн ответ
    answer = find_answer(country, user_lang, user_text)

    if not answer:
        # Если нет оффлайн ответа — вызываем OpenAI GPT-3.5
        prompt = f"Відповідай простою мовою на питання користувача про легалізацію в Польщі.\nПитання: {user_text}"
        try:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ти експерт із легалізації в Польщі."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            answer = response.choices[0].message.content
        except Exception as e:
            logging.error(f"OpenAI error: {e}")
            answer = {
                "uk": "Виникла помилка при отриманні відповіді. Спробуйте пізніше.",
                "ru": "Произошла ошибка при получении ответа. Попробуйте позже.",
                "pl": "Wystąpił błąd podczas uzyskiwania odpowiedzi. Spróbuj później.",
                "en": "An error occurred while getting the answer. Please try again later.",
                "es": "Se produjo un error al obtener la respuesta. Por favor, inténtelo de nuevo más tarde.",
                "id": "Terjadi kesalahan saat mendapatkan jawaban. Silakan coba lagi nanti."
            }.get(user_lang, "Виникла помилка при отриманні відповіді. Спробуйте пізніше.")

    await update.message.reply_text(answer)
    return HANDLE_QUESTION

# Обработка обратной связи
async def handle_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    feedback_text = update.message.text
    user_id = update.message.from_user.id
    logging.info(f"Feedback from user {user_id}: {feedback_text}")

    # Можно сюда добавить отправку в БД или email

    await update.message.reply_text(
        "Дякуємо за ваш відгук! Він дуже важливий для нас.",
        reply_markup=ReplyKeyboardRemove()
    )

    # После фидбека возвращаем в меню с выбором
    keyboard = [
        [KeyboardButton("Задати питання")],
        [KeyboardButton("Залишити відгук")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        "Ви можете задати ще питання або залишити відгук.",
        reply_markup=reply_markup
    )
    return HANDLE_QUESTION

# Команда /cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Дякую, що скористалися ботом! Для початку введіть /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    TOKEN = os.getenv("BOT_TOKEN")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    PORT = int(os.environ.get("PORT", 8000))

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_COUNTRY: [MessageHandler(filters.TEXT & (~filters.COMMAND), select_country)],
            SELECT_LANGUAGE: [MessageHandler(filters.TEXT & (~filters.COMMAND), select_language)],
            HANDLE_QUESTION: [
                MessageHandler(filters.Regex("^(Задати питання|задать вопрос|ask a question|tanyakan pertanyaan|hacer una pregunta)$"), handle_question_or_feedback),
                MessageHandler(filters.Regex("^(Залишити відгук|оставить отзыв|leave feedback|berikan umpan balik|dejar comentarios)$"), handle_question_or_feedback),
                MessageHandler(filters.TEXT & (~filters.COMMAND), handle_question)
            ],
            FEEDBACK: [MessageHandler(filters.TEXT & (~filters.COMMAND), handle_feedback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    app.add_handler(conv_handler)

    # Запуск webhook на Render
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
