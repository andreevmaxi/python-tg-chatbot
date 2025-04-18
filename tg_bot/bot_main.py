import sys
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from dotenv import load_dotenv
import asyncio
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import db

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

# Инициализация OpenAI клиента
openai_client = OpenAI(api_key=os.getenv("OPENAI_KEY"))

# ID ассистента и файла (заполнятся при первом запуске)
ASSISTANT_ID = os.getenv("ASSISTANT_ID") or None
FILE_ID = os.getenv("FILE_ID") or None

translations = {
    "ru": {
        "welcome": "Привет!\n🤖 Я бот Latoken для хакатона от Коробко Максима.\nВыбери, что хочешь узнать:",
        "about_latoken": "🏢 О Латокен",
        "about_hackathon": "💻 О хакатоне",
        "refresh_buttons": "🔄 Обновить кнопки",
        "change_language": "🌐 Язык",
        "choose_language": "Выберите язык:",
        "latoken_info": "Latoken — криптоплатформа для торговли и обучения.\nСсылка: https://coda.io/@latoken/latoken-talent/latoken-161",
        "hackathon_info": "Хакатон — шанс попасть в команду Latoken.\nСсылка: https://deliver.latoken.com/hackathon",
        "unknown": "Используй кнопки для выбора!",
        "buttons_updated": "Кнопки обновлены!",
        "russian_lang": "🇷🇺 Русский",
        "english_lang": "🇬🇧 Английский",
        "keywords": {
            "latoken": ["латокен", "компани", "compan", "latoken"],
            "hackathon": ["хакатон", "мероприяти", "соревновани", "hackathon", "hackaton", "event", "competition"]
        }
    },
    "en": {
        "welcome": "Hello!\n🤖 I am bot Latoken for hackathon from Korobko Maksim.\nChoose what you want to know:",
        "about_latoken": "🏢 About Latoken",
        "about_hackathon": "💻 About Hackathon",
        "refresh_buttons": "🔄 Refresh Buttons",
        "change_language": "🌐 Language",
        "choose_language": "Choose language:",
        "latoken_info": "Latoken - crypto platform for trading and education.\nLink: https://coda.io/@latoken/latoken-talent/latoken-161",
        "hackathon_info": "Hackathon - chance to join Latoken team.\nLink: https://deliver.latoken.com/hackathon",
        "unknown": "Please use the buttons!",
        "buttons_updated": "Buttons updated!",
        "russian_lang": "🇷🇺 Russian",
        "english_lang": "🇬🇧 English",
        "keywords": {
            "latoken": ["латокен", "компани", "compan", "latoken"],
            "hackathon": ["хакатон", "мероприяти", "соревновани", "hackathon", "hackaton", "event", "competition"]
        }
    }
}

async def find_matching_intent(user_id: int, text: str) -> str:
    lang = await db.get_user_language(user_id)
    text = text.lower()

    # Проверка ключевых слов для латокен
    if any(keyword in text for keyword in translations[lang]["keywords"]["latoken"]):
        return "latoken_info"

    # Проверка ключевых слов для хакатона
    if any(keyword in text for keyword in translations[lang]["keywords"]["hackathon"]):
        return "hackathon_info"

    return None

async def get_translation(user_id: int, key: str) -> str:
    lang = await db.get_user_language(user_id)
    return translations[lang].get(key, key)


async def build_main_keyboard(user_id: int):
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text=await get_translation(user_id, "about_latoken")),
        types.KeyboardButton(text=await get_translation(user_id, "about_hackathon"))
    )
    builder.row(
        types.KeyboardButton(text=await get_translation(user_id, "refresh_buttons")),
        types.KeyboardButton(text=await get_translation(user_id, "change_language"))
    )
    return builder.as_markup(resize_keyboard=True)


@dp.message(Command("start", "help"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    await message.answer(
        await get_translation(user_id, "welcome"),
        reply_markup=await build_main_keyboard(user_id)
    )


@dp.message(F.text.in_([t["refresh_buttons"] for t in translations.values()]))
async def refresh_buttons(message: types.Message):
    user_id = message.from_user.id
    await message.answer(
        await get_translation(user_id, "buttons_updated"),
        reply_markup=await build_main_keyboard(user_id)
    )


@dp.message(F.text.in_([t["change_language"] for t in translations.values()]))
async def change_language(message: types.Message):
    user_id = message.from_user.id
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text=await get_translation(user_id, "russian_lang")),
        types.KeyboardButton(text=await get_translation(user_id, "english_lang"))
    )
    await message.answer(
        await get_translation(user_id, "choose_language"),
        reply_markup=builder.as_markup(resize_keyboard=True)
    )


@dp.message(F.text.in_([t["russian_lang"] for t in translations.values()]))
async def set_russian(message: types.Message):
    user_id = message.from_user.id
    await db.set_user_language(user_id, 'ru')
    await message.answer("Язык изменён на Русский ✅")
    await cmd_start(message)


@dp.message(F.text.in_([t["english_lang"] for t in translations.values()]))
async def set_english(message: types.Message):
    user_id = message.from_user.id
    await db.set_user_language(user_id, 'en')
    await message.answer("Language changed to English ✅")
    await cmd_start(message)


@dp.message()
async def handle_buttons(message: types.Message):
    user_id = message.from_user.id
    text = message.text

    if text == await get_translation(user_id, "about_latoken"):
        await message.answer(await get_translation(user_id, "latoken_info"))
    elif text == await get_translation(user_id, "about_hackathon"):
        await message.answer(await get_translation(user_id, "hackathon_info"))

    # Обработка текстовых запросов
    else:
        intent = await find_matching_intent(user_id, text)
        if intent:
            await message.answer(await get_translation(user_id, intent))
        else:
            await message.answer(await get_translation(user_id, "unknown"))


async def main():
    # Инициализация БД
    try:
        await db.connect()
        logging.info("Database connected successfully")
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        return

    # Запуск бота
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        logging.info("Database connection closed")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())