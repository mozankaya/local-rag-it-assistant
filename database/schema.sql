-- ===========================================================
-- Bu dosya uygulamanın güncel PostgreSQL şemasını açıklayan
-- bir referans dosyadır.
--
-- Veritabanı kurulumu için doğrudan çalıştırılmamalıdır.
-- Asıl şema kaynağı backend/alembic/versions altındaki
-- Alembic migration dosyalarıdır.
--
-- Temiz kurulum:
--
--     alembic upgrade head
--
-- Bu dosya mevcut/dolu bir veritabanında topluca
-- çalıştırılmamalıdır.
-- ============================================================


CREATE EXTENSION vector;


CREATE TABLE public.n8n_vector_collections (
    uuid UUID NOT NULL DEFAULT gen_random_uuid(),
    name VARCHAR NULL,
    cmetadata JSONB NULL,

    CONSTRAINT n8n_vector_collections_pkey
        PRIMARY KEY (uuid)
);

CREATE INDEX idx_n8n_vector_collections_name
ON public.n8n_vector_collections (name);



-- n8n ingestion workflow'u doküman parçalarını bu tabloya taşır.
-- RAG sorguları benzer doküman parçalarını bu tablo üzerinden arar.
CREATE TABLE public.langchain_document_chunks (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    text TEXT NULL,
    metadata JSONB NULL,
    embedding VECTOR NULL,
    collection_id UUID NULL,

    CONSTRAINT langchain_document_chunks_pkey
        PRIMARY KEY (id),

    CONSTRAINT langchain_document_chunks_collection_id_fkey
        FOREIGN KEY (collection_id)
        REFERENCES public.n8n_vector_collections (uuid)
        ON DELETE CASCADE
);


-- Güvenli reindex sırasında yeni chunk'lar önce bu tabloya yazılır.
-- Doğrulamalar başarılı olduktan sonra aktif tabloya aktarılır.
CREATE TABLE public.langchain_document_chunks_staging (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    text TEXT NULL,
    metadata JSONB NULL,
    embedding VECTOR NULL,
    collection_id UUID NULL,

    CONSTRAINT langchain_document_chunks_staging_pkey
        PRIMARY KEY (id),

    CONSTRAINT langchain_document_chunks_staging_collection_id_fkey
        FOREIGN KEY (collection_id)
        REFERENCES public.n8n_vector_collections (uuid)
        ON DELETE CASCADE
);


CREATE TABLE public.users (
    id SERIAL NOT NULL,
    email VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now(),

    CONSTRAINT users_pkey
        PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email
ON public.users (email);

CREATE INDEX ix_users_id
ON public.users (id);



-- Chat kayıtları n8n tarafından yazılır.
-- Backend admin dashboard bu tabloyu okur.
CREATE TABLE public.chat_logs (
    id SERIAL NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB NULL,
    category TEXT NULL,
    section_title TEXT NULL,
    response_type TEXT NULL,
    created_at TIMESTAMPTZ NULL DEFAULT CURRENT_TIMESTAMP,
    request_id VARCHAR(100) NULL,
    duration_ms NUMERIC(12, 2) NULL,
    source_count INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT chat_logs_pkey
        PRIMARY KEY (id)
);

CREATE INDEX idx_chat_logs_category
ON public.chat_logs (category);

CREATE INDEX idx_chat_logs_created_at
ON public.chat_logs (created_at);

CREATE INDEX idx_chat_logs_request_id
ON public.chat_logs (request_id);

CREATE INDEX idx_chat_logs_section_title
ON public.chat_logs (section_title);



-- Feedback kayıtları n8n tarafından yazılır.
-- Her feedback kaydı ilgili chat_logs kaydına chat_log_id ile bağlanır.
-- question, answer ve sources alanları analiz amacıyla snapshot olarak korunur.
-- Backend admin dashboard bu tabloyu okur.
CREATE TABLE public.feedback_logs (
    id SERIAL NOT NULL,
    chat_log_id INTEGER NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    feedback TEXT NOT NULL,
    sources JSONB NULL,
    created_at TIMESTAMPTZ NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT feedback_logs_pkey
        PRIMARY KEY (id),

    CONSTRAINT feedback_logs_feedback_check
        CHECK (feedback IN ('useful', 'not_useful')),

    CONSTRAINT uq_feedback_logs_chat_log_id
        UNIQUE (chat_log_id),

    CONSTRAINT fk_feedback_logs_chat_log_id_chat_logs
        FOREIGN KEY (chat_log_id)
        REFERENCES public.chat_logs (id)
        ON DELETE SET NULL
);