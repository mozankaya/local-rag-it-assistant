-- Chat log retention cleanup
-- This query deletes chat logs older than 180 days.
-- It is intended to be executed manually or by a scheduled maintenance job in future versions.

WITH deleted AS (
    DELETE FROM chat_logs
    WHERE created_at < NOW() - INTERVAL '180 days'
    RETURNING id
)
SELECT COUNT(*) AS deleted_count
FROM deleted;