import asyncpg
from typing import Optional, Tuple
import os

class Database:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.pool = None
        return cls._instance

    def get_db_url(self):
        if os.getenv('DOCKER_ENV') == 'true':
            return os.getenv('DOCKER_DB_URL')
        else:
            return os.getenv('LOCAL_DB_URL')

    async def connect(self):
        try:
            self.pool = await asyncpg.create_pool(
                dsn=self.get_db_url(),
                min_size=1,  # Минимальное количество соединений
                max_size=10  # Максимальное количество соединений
            )
            print("✅ Database pool created successfully!")
        except Exception as e:
            print(f"❌ Database connection error: {e}")

    async def close(self):
        """Закрытие подключения"""
        if self.pool:
            await self.pool.close()
            print("Database connection pool closed")

    async def get_user_language(self, user_id: int) -> str:
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT language FROM users WHERE user_id = $1",
                user_id
            ) or 'ru'

    async def set_user_language(self, user_id: int, lang: str):
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users(user_id, language) 
                VALUES($1, $2)
                ON CONFLICT (user_id) 
                DO UPDATE SET language = $2
                """, user_id, lang
            )

    async def get_openai_assets(self) -> Tuple[str, str]:
        """Получение последних OpenAI ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT assistant_id, file_id 
                FROM openai_assets 
                ORDER BY created_at DESC LIMIT 1"""
            )
            return (row['assistant_id'], row['file_id']) if row else (None, None)

    async def save_openai_assets(self, assistant_id: str, file_id: str):
        """Сохранение новых OpenAI ID"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO openai_assets(assistant_id, file_id) 
                VALUES($1, $2)""",
                assistant_id, file_id
            )

    async def get_user_state(self, user_id: int) -> Optional[str]:
        """Получить состояние пользователя (раздел, в котором он находится)"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT state FROM users WHERE user_id = $1",
                user_id
            )

    async def set_user_state(self, user_id: int, state: Optional[str]):
        """Установить или сбросить состояние пользователя"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users(user_id, state) 
                VALUES($1, $2) 
                ON CONFLICT (user_id) 
                DO UPDATE SET state = $2
                """,
                user_id, state
            )

    async def update_culture_summary(self, language: str, summary: str):
        """Обновляет summary_ru или summary_en в БД"""
        async with self.pool.acquire() as conn:
            if language == "ru":
                await conn.execute(
                    "UPDATE culture_deck SET summary_ru = $1 WHERE language = 'ru'", summary
                )
            elif language == "en":
                await conn.execute(
                    "UPDATE culture_deck SET summary_en = $1 WHERE language = 'en'", summary
                )

    async def get_culture_deck(self, language: str) -> Optional[dict]:
        """Получает данные Culture Deck для указанного языка"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT main_content, additional_contents, summary_ru, summary_en, link 
                   FROM culture_deck WHERE language = $1""",
                language
            )
            if row:
                return {
                    "main_content": row["main_content"],
                    "additional_contents": row["additional_contents"],
                    "summary": row["summary_ru"] if language == "ru" else row["summary_en"],
                    "link": row["link"]
                }
            return None

    async def save_culture_deck(self, data: dict):
        """Сохранить данные Culture Deck в БД"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO culture_deck (language, main_content, summary, link)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (language) 
                DO UPDATE SET main_content = $2, summary = $3, link = $4
                """,
                data["language"], data["main_content"], data["summary"], data["link"]
            )
# Синглтон экземпляр
db = Database()