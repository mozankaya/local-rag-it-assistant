import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


LOG_FIELDS = (
    "event",
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "error_type",
)


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for field_name in LOG_FIELDS:
            field_value = getattr(record, field_name, None)

            if field_value is not None:
                log_data[field_name] = field_value

        if record.exc_info:
            log_data["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(
            log_data,
            ensure_ascii=False,
            default=str,
        )


def configure_logging(log_level: str = "INFO") -> None:
    app_logger = logging.getLogger("app")

    resolved_level = getattr(
        logging,
        log_level.upper(),
        logging.INFO,
    )

    app_logger.setLevel(resolved_level)
    app_logger.propagate = False

    has_json_handler = any(
        getattr(handler, "_izeltas_json_handler", False)
        for handler in app_logger.handlers
    )

    if not has_json_handler:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(resolved_level)
        handler.setFormatter(JsonLogFormatter())

        handler._izeltas_json_handler = True  # type: ignore[attr-defined]

        app_logger.addHandler(handler)


    logging.getLogger("uvicorn.access").disabled = True