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
from src.culture_deck_scraper import CultureDeckScraper
from src.ai_integration import OpenAIIntegration

load_dotenv()
bot = Bot(token=os.getenv("TELEGRAM_TOKEN"))
dp = Dispatcher()

scraper = CultureDeckScraper()

# ID ассистента и файла (заполнятся при первом запуске)
ASSISTANT_ID = os.getenv("ASSISTANT_ID") or None
FILE_ID = os.getenv("FILE_ID") or None

translations = {
    "ru": {
        "welcome": "Привет!\n🤖 Я бот Latoken для хакатона от Коробко Максима.\nВыбери, что хочешь узнать:",
        "about_latoken": "🏢 О Латокен",
        "about_hackathon": "💻 О Хакатоне",
        "about_culture_deck": "👥 О Корпоротивной Культуре",
        "refresh_buttons": "🔄 Обновить кнопки",
        "change_language": "🌐 Язык",
        "choose_language": "Выберите язык:",
        "latoken_info": "Latoken — криптоплатформа для торговли и обучения.\nСсылка: https://coda.io/@latoken/latoken-talent/latoken-161",
        "hackathon_info": "Хакатон — шанс попасть в команду Latoken.\nСсылка: https://deliver.latoken.com/hackathon",
        "unknown": "Используй кнопки для выбора!",
        "buttons_updated": "Кнопки обновлены!",
        "russian_lang": "🇷🇺 Русский",
        "english_lang": "🇬🇧 Английский",
        "question_ask": "Что хотите спросить?",
        "know_more": "🔍 Узнать больше",
        "button_back": "🔙 Назад",
        "culture_deck_summary": "Краткое содержание корпоротивной культуры: ",
        "link_word": "Ссылка: ",
        "keywords": {
            "latoken": ["латокен", "компани", "compan", "latoken"],
            "hackathon": ["хакатон", "мероприяти", "соревновани", "hackathon", "hackaton", "event", "competition"]
        }
    },
    "en": {
        "welcome": "Hello!\n🤖 I am bot Latoken for hackathon from Korobko Maksim.\nChoose what you want to know:",
        "about_latoken": "🏢 About Latoken",
        "about_hackathon": "💻 About Hackathon",
        "about_culture_deck": "👥 About Corporate Culture",
        "refresh_buttons": "🔄 Refresh Buttons",
        "change_language": "🌐 Language",
        "choose_language": "Choose language:",
        "latoken_info": "Latoken - crypto platform for trading and education.\nLink: https://coda.io/@latoken/latoken-talent/latoken-161",
        "hackathon_info": "Hackathon - chance to join Latoken team.\nLink: https://deliver.latoken.com/hackathon",
        "unknown": "Please use the buttons!",
        "buttons_updated": "Buttons updated!",
        "russian_lang": "🇷🇺 Russian",
        "english_lang": "🇬🇧 English",
        "question_ask": "What you want to ask?",
        "know_more": "🔍 Know more",
        "button_back": "🔙 back",
        "culture_deck_summary": "Quick summary for culture deck: ",
        "link_word": "Link: ",
        "keywords": {
            "latoken": ["латокен", "компани", "compan", "latoken"],
            "hackathon": ["хакатон", "мероприяти", "соревновани", "hackathon", "hackaton", "event", "competition"]
        }
    }
}

async def get_culture_deck_data():
    data = await db.get_culture_deck()
    if not data:
        data = scraper.get_content("https://coda.io/@latoken/latoken-talent/culture-139")
        await db.save_culture_deck(data)
    return data

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
        types.KeyboardButton(text=await get_translation(user_id, "about_culture_deck"))
    )
    builder.row(
        types.KeyboardButton(text=await get_translation(user_id, "refresh_buttons")),
        types.KeyboardButton(text=await get_translation(user_id, "change_language"))
    )
    await db.set_user_state(user_id, 'base')
    return builder.as_markup(resize_keyboard=True)


@dp.message(Command("start", "help"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    await message.answer(
        await get_translation(user_id, "welcome"),
        reply_markup=await build_main_keyboard(user_id)
    )


async def get_culture_deck_summary(user_id: int):
    lang = await db.get_user_language(user_id)
    data = await db.get_culture_deck(lang)
    return {
        "summary": data["summary"],
        "link": data["link"]
    }

@dp.message(F.text.in_([t["about_culture_deck"] for t in translations.values()]))
async def culture_deck_info(message: types.Message):
    user_id = message.from_user.id
    keyboard = ReplyKeyboardBuilder()
    keyboard.row(
        types.KeyboardButton(text=await get_translation(user_id, "know_more")),
        types.KeyboardButton(text=await get_translation(user_id, "button_back"))
    )
    await db.set_user_state(user_id, 'culture_deck')

    await message.answer(
        await get_translation(user_id,"question_ask"),
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )


@dp.message(F.text.in_([t["know_more"] for t in translations.values()]))
async def know_more(message: types.Message):
    user_id = message.from_user.id
    data = await get_culture_deck_summary(user_id)
    await message.answer(
        await get_translation(user_id, "culture_deck_summary")
        + data["summary"]
        + "\n" + await get_translation(user_id, "link_word")
        + data["link"]
    )


@dp.message(F.text.in_([t["button_back"] for t in translations.values()]))
async def back_to_main(message: types.Message):
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

@dp.message()
async def handle_culture_deck_questions(message: types.Message):
    user_id = message.from_user.id
    user_state = await db.get_user_state(user_id)

    if user_state == "culture_deck":
        # Пользователь в разделе Culture Deck — передаем его вопрос OpenAI
        lang = await db.get_user_language(user_id)
        data = await db.get_culture_deck(lang)

        response = await openai_client.ask_about_culture_deck(message.text, data["main_content"], data["additional_contents"])
        await message.answer(response)
    else:
        await handle_buttons(message)


async def main():
    # Инициализация БД
    try:
        await db.connect()
        logging.info("Database connected successfully")

        # Инициализация OpenAI клиента
        openai_client = OpenAIIntegration(os.getenv("OPENAI_KEY"))
        logging.info("Openai client created successfully")

        # Проверяем русский Culture Deck
        culture_data_ru = await db.get_culture_deck("ru")
        if not culture_data_ru or culture_data_ru["summary"] is None or culture_data_ru["summary"] == '':
            print("Отсутствует summary_ru, генерируем...")
            raw_data = scraper.get_content("https://coda.io/@latoken/latoken-talent/culture-139")
            summary = await openai_client.generate_summaries(raw_data["main_content"], "ru")
            await db.update_culture_summary("ru", summary)

        # Проверяем английский Culture Deck
        culture_data_en = await db.get_culture_deck("en")
        if not culture_data_en or culture_data_en["summary"] is None or culture_data_en["summary"] == '':
            print("Отсутствует summary_en, генерируем...")
            raw_data = scraper.get_content("https://coda.io/@latoken/latoken-talent/culture-139")
            summary= await openai_client.generate_summaries(raw_data["main_content"], "en")
            await db.update_culture_summary("en", summary)
        logging.info("Culture Deck summary is up to date.")
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