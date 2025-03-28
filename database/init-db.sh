#!/bin/bash
psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} <<-END
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    language VARCHAR(2) NOT NULL DEFAULT 'ru'
);

CREATE TABLE IF NOT EXISTS openai_assets (
    id SERIAL PRIMARY KEY,
    assistant_id VARCHAR(50),
    file_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_user_id ON users(user_id);
END