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
        """Инициализация подключения к БД"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                dsn=self.get_db_url(),
                min_size=5,
                max_size=20,
                command_timeout=30
            )
            print("Database connection pool created")

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

# Синглтон экземпляр
db = Database()