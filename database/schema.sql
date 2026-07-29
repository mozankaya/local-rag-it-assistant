CREATE EXTENSION IF NOT EXISTS vector;


-- ============================================================
-- RAG DOKÜMAN TABLOSU
-- ============================================================

-- LangChain / n8n PGVector Store tarafından kullanılan
-- aktif RAG doküman tablosu.
--
-- Bu tablo n8n workflow tarafından da oluşturulabilir.
-- Burada temiz kurulum için tutulur.

CREATE TABLE IF NOT EXISTS langchain_document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT,
    metadata JSONB,
    embedding vector(768)
);


-- ============================================================
-- KULLANICI TABLOSU
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- CHAT LOG TABLOSU
-- ============================================================

-- request_id, duration_ms ve source_count alanları
-- Alembic migration'ı tarafından eklenecektir.

CREATE TABLE IF NOT EXISTS chat_logs (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB,
    category TEXT,
    section_title TEXT,
    response_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- FEEDBACK LOG TABLOSU
-- ============================================================

CREATE TABLE IF NOT EXISTS feedback_logs (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    feedback TEXT NOT NULL
        CHECK (feedback IN ('useful', 'not_useful')),
    sources JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- CHAT LOG INDEXLERİ
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_chat_logs_created_at
ON chat_logs (created_at);

CREATE INDEX IF NOT EXISTS idx_chat_logs_category
ON chat_logs (category);

CREATE INDEX IF NOT EXISTS idx_chat_logs_section_title
ON chat_logs (section_title);

CREATE INDEX IF NOT EXISTS idx_chat_logs_response_type
ON chat_logs (response_type);


-- ============================================================
-- FEEDBACK LOG INDEXLERİ
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_feedback_logs_created_at
ON feedback_logs (created_at);

CREATE INDEX IF NOT EXISTS idx_feedback_logs_feedback
ON feedback_logs (feedback);


-- ============================================================
-- KULLANICI INDEXLERİ
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_users_email
ON users (email);

CREATE INDEX IF NOT EXISTS idx_users_role
ON users (role);