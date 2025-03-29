#!/bin/bash
psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} <<-END
-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    language VARCHAR(2) NOT NULL DEFAULT 'ru',
    state VARCHAR(50) DEFAULT NULL -- Состояние пользователя (раздел, где он находится)
);

-- Таблица данных Culture Deck
CREATE TABLE IF NOT EXISTS culture_deck (
    id SERIAL PRIMARY KEY,
    language VARCHAR(2) NOT NULL UNIQUE,
    main_content TEXT NOT NULL,
    additional_contents TEXT,
    summary_ru TEXT,
    summary_en TEXT,
    link TEXT NOT NULL
);

INSERT INTO culture_deck (language, main_content, additional_contents, summary_ru, summary_en, link)
VALUES ('ru', '', '', '', '', 'https://coda.io/@latoken/latoken-talent/culture-139')
ON CONFLICT (language) DO NOTHING;

INSERT INTO culture_deck (language, main_content, additional_contents, summary_ru, summary_en, link)
VALUES ('en', '', '', '', '', 'https://coda.io/@latoken/latoken-talent/culture-139')
ON CONFLICT (language) DO NOTHING;

-- Таблица OpenAI ассетов
CREATE TABLE IF NOT EXISTS openai_assets (
    id SERIAL PRIMARY KEY,
    assistant_id VARCHAR(50),
    file_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_culture_deck_language ON culture_deck(language);
END
