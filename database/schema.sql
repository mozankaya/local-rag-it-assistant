CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT,
    section_title TEXT,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE INDEX IF NOT EXISTS idx_chat_logs_created_at
ON chat_logs (created_at);

CREATE INDEX IF NOT EXISTS idx_chat_logs_category
ON chat_logs (category);

CREATE INDEX IF NOT EXISTS idx_chat_logs_section_title
ON chat_logs (section_title);