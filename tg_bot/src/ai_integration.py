import asyncio
import os
from openai import AsyncOpenAI

from tg_bot.src.database import Database
from tg_bot.src.culture_deck_scraper import CultureDeckScraper

class OpenAIIntegration:
    def __init__(self, api_key_gen):
        self.client = AsyncOpenAI(api_key=api_key_gen)
        self.scraper = CultureDeckScraper()
        self.db = Database()


    async def init_assistant(self):
        try:
            await self.db.connect()
            print("Database connected for ai successfully")
        except Exception as e:
            print(f"Database connection for ai error: {e}")
            return
        """Инициализация ассистента: загружаем данные, если их нет"""
        assistant_id, file_id = await self.db.get_openai_assets()

        if assistant_id and file_id:
            print("Используем существующего ассистента")
            return assistant_id

        print("Создаём нового ассистента...")

        # Создаём временный файл
        file_path = "culture_deck.md"
        with open(file_path, "w") as f:
            f.write(self.scraper.get_content("https://coda.io/@latoken/latoken-talent/culture-139"))

        # Загружаем файл в OpenAI
        file = await self.client.files.create(
            file=open(file_path, "rb"),
            purpose="assistants"
        )

        # Создаем ассистента
        assistant = await self.client.beta.assistants.create(
            name="Latoken Culture Expert",
            instructions="Ты HR-ассистент Latoken. Используй загруженный файл, чтобы отвечать на вопросы о культуре компании.",
            model="gpt-4-turbo",
            tools=[{"type": "retrieval"}],
            file_ids=[file.id]
        )

        # Сохраняем ассистента в БД
        await self.db.save_openai_assets(assistant.id, file.id)

        return assistant.id

    @staticmethod
    async def ask_about_culture_deck(question: str, language: str) -> str:
        """Отвечает на вопросы, используя данные Culture Deck"""
        data = await self.db.get_culture_deck(language)

        if not data:
            return "Извините, информация пока недоступна."

        context = f"{data['main_content']}\n\nДополнительная информация:\n{data['additional_contents']}"

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = f"Ответь на вопрос на {language} используя следующий текст:\n{context}\n\nВопрос: {question}"

        response = await client.completions.create(
            model="gpt-4-turbo", prompt=prompt, max_tokens=200
        )

        return response.choices[0].text.strip() if response else "Ошибка: нет ответа."


    @staticmethod
    async def generate_summaries(content: str, lang) -> str:
        """Генерирует краткое описание Culture Deck на русском и английском"""
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if (lang == "en"):
            prompt = f"Create a short summary (3-4 sentences) for the following text:\n{content[:1000]}..."
        else:
            prompt = f"Создай краткое описание (3-4 предложения) для следующего текста:\n{content[:1000]}..."

        response = await asyncio.gather(
            client.completions.create(model="gpt-4-turbo", prompt=prompt, max_tokens=150)
        )

        return response[0].text.strip()
