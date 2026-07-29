-- Chat ve feedback kayıtları için saklama süresi temizliği.
-- Bu sorgu 30 günden eski kayıtları siler.
--
-- Temizlik işlemi normalde zamanlanmış
-- "Database Retention Cleanup" n8n workflow'u tarafından
-- her gün otomatik olarak çalıştırılır.
--
-- Gerektiğinde bu dosya DBeaver veya psql üzerinden
-- manuel olarak da çalıştırılabilir.

WITH deleted_chat_logs AS (
    DELETE FROM public.chat_logs
    WHERE created_at < NOW() - INTERVAL '30 days'
    RETURNING id
),
deleted_feedback_logs AS (
    DELETE FROM public.feedback_logs
    WHERE created_at < NOW() - INTERVAL '30 days'
    RETURNING id
)
SELECT
    (
        SELECT COUNT(*)
        FROM deleted_chat_logs
    ) AS deleted_chat_log_count,
    (
        SELECT COUNT(*)
        FROM deleted_feedback_logs
    ) AS deleted_feedback_log_count;