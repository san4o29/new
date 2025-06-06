import os
import logging
from openai import OpenAI
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
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
PORT = int(os.environ.get("PORT", 8000))

# OpenAI клієнт
client = OpenAI(api_key=OPENAI_API_KEY)

# База знань
faq_data = {
    "україна": {
        "uk": [
            {
                "keywords": ["карта побиту", "тимчасове перебування", "документи на карту"],
                "answer": "Громадяни України можуть подати на карту побиту на підставі роботи, навчання або родинних зв’язків. Заява подається до Воєводського управління за місцем проживання. Необхідно підготувати паспорт, фото, підтвердження доходів, медичну страховку, договір оренди та інші документи.\nПроцес може займати 3–6 місяців.",
                "advice": "Зберігайте копії всіх документів та подавайте заяву рекомендованим листом з повідомленням про вручення."
            },
            {
                "keywords": ["тимчасовий захист", "status UKR", "захист для українців"],
                "answer": "Польща надала тимчасовий захист (status UKR) українцям, які прибули після 24 лютого 2022 року. Він дозволяє легальне перебування, доступ до ринку праці, освіти та медичних послуг.",
                "advice": "Зареєструйтеся у системі PESEL якнайшвидше для повного доступу до прав."
            },
            {
                "keywords": ["робота", "дозвіл на роботу", "працевлаштування"],
                "answer": "Українці можуть працювати в Польщі без дозволу на роботу за умови повідомлення працедавцем через портал praca.gov.pl. Це правило стосується осіб з тимчасовим захистом, візою або іншим дозволеним перебуванням.",
                "advice": "Перевіряйте, чи роботодавець справді подав повідомлення до Urząd Pracy."
            }
        ]
    },
    "білорусь": {
        "ru": [
            {
                "keywords": ["карта побыту", "воеводское приглашение", "легализация"],
                "answer": "Граждане Беларуси могут подать на карту побыту на основании работы, бизнеса, учёбы или воссоединения семьи. Процедура такая же, как и для других иностранцев: подача заявления, сбор документов, ожидание решения.\nСрок рассмотрения — от 3 до 8 месяцев.",
                "advice": "Храните подтверждения подачи документов, особенно если вы подаётесь по почте."
            },
            {
                "keywords": ["работа", "официальное трудоустройство", "разрешение"],
                "answer": "Для официальной работы в Польше белорусам требуется разрешение на работу типа A или карта побыту с правом на труд.\nНекоторые работодатели могут получить разрешение централизованно через воеводство.",
                "advice": "Убедитесь, что у вас есть копия разрешения на работу, выданная работодателем."
            }
        ]
    },
    "молдова": {
        "ru": [
            {
                "keywords": ["безвиз", "работа", "легализация"],
                "answer": "Граждане Молдовы могут пребывать в Польше до 90 дней без визы. Для легального проживания и работы нужно подать заявление на карту побыту.\nНеобходимо иметь контракт, страхование, жильё и подтверждение доходов.",
                "advice": "Подавайте заявление до окончания безвизового периода."
            }
        ]
    },
    "грузія": {
        "ru": [
            {
                "keywords": ["виза", "карта побыту", "проживание"],
                "answer": "Граждане Грузии могут пребывать в Польше до 90 дней без визы. Для проживания и работы нужно оформить карту побыту или получить визу типа D.\nПри подаче важно предоставить все документы, включая медицинскую страховку.",
                "advice": "Проверяйте актуальные правила въезда на сайте польского МИД."
            }
        ]
    },
    "індонезія": {
        "id": [
            {
                "keywords": ["izin tinggal", "kartu tinggal", "visa kerja"],
                "answer": "Warga negara Indonesia harus memiliki visa kerja (tipe D) atau izin tinggal untuk tinggal dan bekerja di Polandia.\nPermohonan dilakukan di kantor Voivodeship dan memerlukan dokumen seperti paspor, kontrak kerja, dan asuransi.",
                "advice": "Ajukan aplikasi sedini mungkin sebelum visa Anda habis masa berlakunya."
            }
        ]
    },
    "колумбія": {
        "es": [
            {
                "keywords": ["residencia", "trabajar", "permiso de trabajo"],
                "answer": "Los ciudadanos colombianos necesitan una visa nacional tipo D para trabajar o residir legalmente en Polonia.\nPosteriormente pueden solicitar la tarjeta de residencia temporal ('karta pobytu').",
                "advice": "Asegúrese de tener un contrato de trabajo válido antes de iniciar el proceso."
            }
        ]
    },
    "філіпіни": {
        "en": [
            {
                "keywords": ["residence permit", "work permit", "visa"],
                "answer": "Citizens of the Philippines need a national D visa and a work permit to stay and work legally in Poland.\nLater, they can apply for a temporary residence card ('karta pobytu').",
                "advice": "Make sure your employer provides the correct documents for your visa application."
            }
        ]
    },
    "непал": {
        "en": [
            {
                "keywords": ["work in poland", "residence card", "legal stay"],
                "answer": "Nepali citizens must apply for a national visa and work permit before entering Poland.\nTo stay long-term, you will need to apply for a residence card through the voivodeship office.",
                "advice": "Be cautious with agencies—verify job offers before applying for a visa."
            }
        ]
    }
}

# Визначення мови
def detect_language(text):
    try:
        return detect(text)
    except:
        return "unknown"

# Пошук відповіді
def find_answer(user_text, user_lang):
    for country, langs in faq_data.items():
        for lang, questions in langs.items():
            if user_lang == lang:
                for q in questions:
                    if any(keyword.lower() in user_text.lower() for keyword in q["keywords"]):
                        return f"{q['answer']}\n\n💡 {q['advice']}"
    return None

# Обробка команди /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Україна 🇺🇦", "Білорусь 🇧🇾"], ["Молдова 🇲🇩", "Грузія 🇬🇪"],
                ["Індонезія 🇮🇩", "Колумбія 🇨🇴"], ["Філіпіни 🇵🇭", "Непал 🇳🇵"],
                ["Зворотній зв'язок"]]
    await update.message.reply_text(
        "🌍 Оберіть вашу країну походження:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

# Обробка повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    lang = detect_language(user_message)
    answer = find_answer(user_message, lang)

    if answer:
        await update.message.reply_text(answer)
    else:
        try:
            prompt = f"Користувач задає питання про легалізацію в Польщі. Відповідай простою мовою. Питання: {user_message}"
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ти експерт із легалізації в Польщі."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            await update.message.reply_text(response.choices[0].message.content)
        except Exception as e:
            logging.error(f"OpenAI error: {e}")
            await update.message.reply_text("⚠️ Помилка при отриманні відповіді. Спробуйте пізніше.")

# Запуск бота через webhook
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    main()
