import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
import asyncio
import openai

load_dotenv()
# Настройки
API_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Расширенная база знаний
knowledge_base = {
    "латокен": {
        "keywords": ["латокен", "компани", "latoken"],
        "response": "Latoken — криптоплатформа для торговли и обучения.\nСсылка: https://coda.io/@latoken/latoken-talent/latoken-161"
    },
    "хакатон": {
        "keywords": ["хакатон", "соревновани", "мероприяти", "hackathon", "hackaton"],
        "response": "Хакатон — шанс попасть в команду Latoken.\nСсылка: https://deliver.latoken.com/hackathon"
    }
}

def find_matching_intent(text: str):
    text = text.lower()
    for intent, data in knowledge_base.items():
        if any(keyword in text for keyword in data["keywords"]):
            return data["response"]
    return None

async def send_welcome(message: types.Message, is_update: bool = False):
    # Создаём кнопки
    buttons = [
        [types.KeyboardButton(text="О Латокен"), types.KeyboardButton(text="О хакатоне")],
        [types.KeyboardButton(text="Обновить кнопки")]
    ]

    # Создаём клавиатуру
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

    # Выбираем текст сообщения
    text = "Клавиатура обновлена!" if is_update else "Привет! Я бот Latoken для хакатона от Коробко Максима. Что хочешь узнать?"

    await message.answer(text, reply_markup=keyboard)


@dp.message(Command("start", "help"))
async def cmd_start(message: types.Message):
    await send_welcome(message)


@dp.message()
async def answer_question(message: types.Message):
    user_text = message.text.lower()

    if user_text == "обновить кнопки":
        await send_welcome(message, is_update=True)
        return #to not duplicate responce

    # Ответы на кнопки
    button_responses = {
        "о латокен": knowledge_base["латокен"]["response"],
        "о хакатоне": knowledge_base["хакатон"]["response"]
    }

    if user_text in button_responses:
        await message.answer(button_responses[user_text])
        return

    # NLP-обработка для произвольных вопросов
    response = find_matching_intent(user_text)

    if response:
        await message.answer(response)
    else:
        await message.answer("Я могу рассказать о:\n- Компании Latoken\n- Хакатоне\n- Процессе интервью\nИспользуй кнопки или напиши вопрос!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())