-- Chat ve feedback kayıtları için saklama süresi temizliği.
-- Bu sorgu 30 günden eski kayıtları siler.
-- Şimdilik manuel olarak çalıştırılabilir.
-- İleride zamanlanmış bir n8n bakım workflow'u tarafından çalıştırılacaktır.

WITH deleted_chat_logs AS (
    DELETE FROM chat_logs
    WHERE created_at < NOW() - INTERVAL '30 days'
    RETURNING id
),
deleted_feedback_logs AS (
    DELETE FROM feedback_logs
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