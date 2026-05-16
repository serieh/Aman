-- Aman Database Schema
-- Run this script to initialize all tables in PostgreSQL
-- Usage: psql -U postgres -d postgres -f init.sql

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                VARCHAR(150) NOT NULL,
    email               VARCHAR(255) UNIQUE NOT NULL,
    password            TEXT NOT NULL,
    preferred_language  VARCHAR(10) DEFAULT 'auto',
    country             VARCHAR(100),
    creation_date       TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Chats Table
CREATE TABLE IF NOT EXISTS chats (
    chat_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title           VARCHAR(255),
    creation_date   TIMESTAMPTZ DEFAULT NOW(),
    modify_date     TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Messages Table
CREATE TABLE IF NOT EXISTS messages (
    message_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id         UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    creation_date   TIMESTAMPTZ DEFAULT NOW(),
    emotional_state JSONB,
    safety_flag     TEXT,
    is_active       BOOLEAN DEFAULT TRUE
);

-- 4. Summaries Table
CREATE TABLE IF NOT EXISTS summaries (
    summary_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id         UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    emotional_state JSONB,
    safety_flag     TEXT,
    version         INTEGER NOT NULL DEFAULT 1,
    creation_date   TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id_active ON messages(chat_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_summaries_chat_id_version ON summaries(chat_id, version DESC);
