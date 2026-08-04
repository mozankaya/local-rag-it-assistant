import logging
import re
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


logger = logging.getLogger("app.request")

REQUEST_ID_HEADER = "X-Request-ID"

VALID_REQUEST_ID_PATTERN = re.compile(
    r"^[A-Za-z0-9._-]{1,100}$"
)


def resolve_request_id(request: Request) -> str:
    """Reuse only a safe client request ID; otherwise generate a local ID."""

    incoming_request_id = request.headers.get(
        REQUEST_ID_HEADER
    )

    if (
        incoming_request_id
        and VALID_REQUEST_ID_PATTERN.fullmatch(
            incoming_request_id
        )
    ):
        return incoming_request_id

    return uuid4().hex


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a safe request ID and emit one structured completion or failure log per request."""

    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        request_id = resolve_request_id(request)
        request.state.request_id = request_id

        started_at = perf_counter()
        status_code = 500
        error_type: str | None = None

        try:
            response = await call_next(request)
            status_code = response.status_code

            response.headers[REQUEST_ID_HEADER] = request_id

            return response

        except Exception as exc:
            error_type = type(exc).__name__
            raise

        finally:
            duration_ms = round(
                (perf_counter() - started_at) * 1000,
                2,
            )

            log_level = (
                logging.ERROR
                if status_code >= 500
                else logging.INFO
            )

            event_name = (
                "request_failed"
                if error_type
                else "request_completed"
            )

            logger.log(
                log_level,
                event_name,
                extra={
                    "event": event_name,
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "error_type": error_type,
                },
            )