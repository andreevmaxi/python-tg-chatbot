import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from tg_bot.src.database import Database
from tg_bot.src.culture_deck_scraper import CultureDeckScraper

load_dotenv()

class OpenAIIntegration:
    def __init__(self, api_key_gen):
        self.client = AsyncOpenAI(api_key=api_key_gen)
        self.scraper = CultureDeckScraper()
        self.db = Database()

    async def init_assistant(self):
        try:
            await self.db.connect()
            print("Database connected for AI successfully")
        except Exception as e:
            print(f"Database connection for AI error: {e}")
            return

        """Инициализация ассистента: загружаем данные, если их нет"""
        assistant_id, _ = await self.db.get_openai_assets()

        if assistant_id:
            print("Используем существующего ассистента")
            return assistant_id

        print("Создаём нового ассистента...")

        # Создаем ассистента без файлов (если они не нужны)
        assistant = await self.client.beta.assistants.create(
            name="Latoken Culture Expert",
            instructions="Ты HR-ассистент Latoken. Отвечай на вопросы о культуре компании.",
            model="gpt-4o",
            tools=[{"type": "retrieval"}]
        )

        # Сохраняем ассистента в БД
        await self.db.save_openai_assets(assistant.id, None)  # File ID не нужен

        return assistant.id

    async def ask_about_culture_deck(self, question: str, language: str) -> str:
        """Отвечает на вопросы, используя данные Culture Deck"""
        data = await self.db.get_culture_deck(language)

        if not data:
            return "Извините, информация пока недоступна."

        context = f"{data['main_content']}\n\nДополнительная информация:\n{data['additional_contents']}"

        prompt = f"Ответь на вопрос на {language} используя следующий текст:\n{context}\n\nВопрос: {question}"

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Ты HR-ассистент Latoken. Используй предоставленный контент для ответов."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )

        return response.choices[0].message.content.strip() if response.choices else "Ошибка: нет ответа."

    async def generate_summaries(self, content: str, lang) -> str:
        """Генерирует краткое описание Culture Deck на русском и английском"""

        prompt = (
            f"Create a short summary (3-4 sentences) for the following text:\n{content[:1000]}..."
            if lang == "en"
            else f"Создай краткое описание (3-4 предложения) для следующего текста:\n{content[:1000]}..."
        )

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Сгенерируй краткое описание текста."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )

        return response.choices[0].message.content.strip() if response.choices else "Ошибка генерации описания."
